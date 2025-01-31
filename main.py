import os
import sys
import yaml
import json
import logging
import paramiko
import concurrent.futures
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from a2wsgi import ASGIMiddleware

logging.basicConfig(level=logging.DEBUG)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
app = FastAPI()

def load_config():
    config_path = BASE_DIR / 'configs' / 'iral_config.yaml'
    sample_config_path = BASE_DIR / 'configs' / 'sample_config.yaml'
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        if not sample_config_path.exists():
            sample_config = {
                "servers": [
                    {
                        "name": "GPU Server 1",
                        "hostname": "example1.domain.com",
                        "port": 22,
                        "username": "ubuntu"
                    }
                ]
            }
            with open(sample_config_path, 'w') as f:
                yaml.dump(sample_config, f, default_flow_style=False)
        raise HTTPException(
            status_code=500,
            detail="Server configuration not found. Please set up config.yaml"
        )
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML: {e}")
        raise HTTPException(status_code=500, detail="Error parsing server configuration")


def fetch_gpu_data_sync(hostname, port, username):
    import socket
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_key_path = os.path.expanduser('~/.ssh/id_rsa')
        if not os.path.exists(ssh_key_path):
            for alt in ['id_ed25519', 'id_ecdsa', 'id_dsa']:
                alt_path = os.path.expanduser(f'~/.ssh/{alt}')
                if os.path.exists(alt_path):
                    ssh_key_path = alt_path
                    break

        try:
            ssh_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
        except:
            ssh_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)

        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            pkey=ssh_key,
            look_for_keys=True,
            timeout=10
        )

        stdin, stdout, stderr = client.exec_command("""
            nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,process_name --format=csv,noheader,nounits &&
            echo "===SEPARATOR===" &&
            nvidia-smi --query-gpu=gpu_uuid,index,name,memory.total,memory.used,temperature.gpu,pstate,utilization.gpu --format=csv,noheader,nounits
        """)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if error:
            logging.error(f"nvidia-smi error on {hostname}:{port} => {error}")

        process_info, gpu_info = output.split("===SEPARATOR===")

        processes = {}
        pids = []
        for line in process_info.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) == 4:
                    gpu_uuid, pid, used_mem, pname = [p.strip() for p in parts]
                    processes.setdefault(gpu_uuid, []).append({
                        "pid": pid,
                        "used_memory": used_mem,
                        "process_name": pname
                    })
                    pids.append(pid)

        if pids:
            cmd_pids = " ".join(pids)
            stdin, stdout, stderr = client.exec_command(
                f"ps -o pid=,user= -p {cmd_pids}"
            )
            user_out = stdout.read().decode().strip()
            pid_to_user = {}
            for l in user_out.split('\n'):
                if l.strip():
                    pval, usr = l.split()
                    pid_to_user[pval] = usr

            for g in processes:
                for proc in processes[g]:
                    proc["username"] = pid_to_user.get(proc["pid"], "unknown")

        gpu_list = []
        for line in gpu_info.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) == 8:
                    gpu_uuid, idx, name, total_mem, used_mem, temp, pstate, util = [x.strip() for x in parts]
                    gpu_list.append({
                        "gpu_id": idx,
                        "gpu_name": name,
                        "total_memory": total_mem,
                        "ram_used": used_mem,
                        "temperature": temp,
                        "pstate": pstate,
                        "utilization": util,
                        "processes": processes.get(gpu_uuid, []),
                        "is_used": len(processes.get(gpu_uuid, [])) > 0
                    })
        return gpu_list

    except Exception as e:
        logging.error(f"SSH error {hostname}:{port} => {e}")
        return [{"error": str(e)}]
    finally:
        client.close()


async def gather_all_servers():
    config = load_config()
    servers = config.get("servers", [])
    loop = asyncio.get_running_loop()

    tasks = []
    with concurrent.futures.ProcessPoolExecutor() as pool:
        for s in servers:
            f = loop.run_in_executor(
                pool,
                fetch_gpu_data_sync,
                s["hostname"],
                s["port"],
                s.get("username", "ubuntu")
            )
            tasks.append((s, f))

        results = []
        for s, fut in tasks:
            gpus = await fut
            results.append({
                "name": s["name"],
                "server": f"{s['hostname']}:{s['port']}",
                "gpus": gpus
            })
    return results


@app.get("/api/servers")
def get_servers():
    cfg = load_config()
    out = []
    for srv in cfg.get("servers", []):
        out.append({
            "name": srv["name"],
            "server": f"{srv['hostname']}:{srv['port']}"
        })
    return out


@app.get("/api/gpus/stream")
async def sse_gpus_stream(request: Request):
    async def event_generator():
        REFRESH_SECONDS = 5
        while True:
            all_data = await gather_all_servers()
            for data in all_data:
                yield f"data: {json.dumps(data)}\n\n"

            if await request.is_disconnected():
                break

            await asyncio.sleep(REFRESH_SECONDS)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


@app.get("/")
def root_index():
    idx_path = STATIC_DIR / "index2.html"
    if idx_path.exists():
        return FileResponse(str(idx_path))
    else:
        raise HTTPException(status_code=404, detail="index.html not found")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    raise RuntimeError("No static directory found.")

wsgi_app = ASGIMiddleware(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
