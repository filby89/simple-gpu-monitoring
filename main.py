import os
import yaml
import paramiko
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json

app = FastAPI()

def load_config():
    """Load server configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), 'configs/iral_config.yaml')
    sample_config_path = os.path.join(os.path.dirname(__file__), 'configs/sample_config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        print("Please copy config.sample.yaml to config.yaml and update with your settings")
        
        # Check if sample config exists, if not create it
        if not os.path.exists(sample_config_path):
            sample_config = {
                'servers': [
                    {
                        'name': 'GPU Server 1',
                        'hostname': 'example1.domain.com',
                        'port': 22
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
        print(f"Error parsing config file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error parsing server configuration"
        )

def get_gpus_from_server(hostname, port, username):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname, port=port, username=username)
        
        # Rest of the function remains the same
        stdin, stdout, stderr = client.exec_command("""
            nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,process_name --format=csv,noheader,nounits &&
            echo "===SEPARATOR===" &&
            nvidia-smi --query-gpu=gpu_uuid,index,name,memory.total,memory.used,temperature.gpu,pstate --format=csv,noheader,nounits
        """)
        output = stdout.read().decode().strip()
        
        # Split the output
        process_info, gpu_info = output.split("===SEPARATOR===")
        
        # Parse process information first
        processes = {}
        pids = []  # Collect all PIDs
        for line in process_info.split('\n'):
            if line.strip():
                gpu_uuid, pid, used_memory, process_name = line.strip().split(',')
                if gpu_uuid not in processes:
                    processes[gpu_uuid] = []
                processes[gpu_uuid].append({
                    "pid": pid.strip(),
                    "used_memory": used_memory.strip(),
                    "process_name": process_name.strip()
                })
                pids.append(pid.strip())

        # Get usernames for all PIDs in a single command
        if pids:
            pid_list = " ".join(pids)
            stdin, stdout, stderr = client.exec_command(f"ps -o pid=,user= -p {pid_list}")
            user_output = stdout.read().decode().strip()
            
            # Create PID to username mapping
            pid_to_user = {}
            for line in user_output.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[0].strip()
                        username = parts[1].strip()
                        pid_to_user[pid] = username

            # Add usernames to processes
            for gpu_uuid in processes:
                for process in processes[gpu_uuid]:
                    process["username"] = pid_to_user.get(process["pid"], "unknown")

        # Parse GPU information
        gpu_list = []
        for line in gpu_info.split('\n'):
            if line.strip():
                gpu_uuid, index, name, total_memory, memory_used, temp, pstate = line.strip().split(',')
                gpu_processes = processes.get(gpu_uuid, [])
                gpu_list.append({
                    "gpu_id": index.strip(),
                    "gpu_name": name.strip(),
                    "total_memory": total_memory.strip(),
                    "ram_used": memory_used.strip(),
                    "temperature": temp.strip(),
                    "pstate": pstate.strip(),
                    "processes": gpu_processes,
                    "is_used": len(gpu_processes) > 0
                })
                
        return gpu_list
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        client.close()

@app.get("/api/gpus")
async def get_gpus():
    config = load_config()
    all_gpus = []
    
    for server in config['servers']:
        server_gpus = get_gpus_from_server(server['hostname'], server['port'], server['username'])
        all_gpus.append({
            "name": server["name"],
            "server": f"{server['hostname']}:{server['port']}",
            "gpus": server_gpus
        })
    
    return all_gpus

# Mount static files directory AFTER the API routes
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at the root
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

if __name__ == "__main__":
    import uvicorn
    try:
        # Test configuration loading at startup
        load_config()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Error starting server: {e}")