# GPU Monitor

## ⚠️ Development Disclaimer
This project was primarily developed with the assistance of Anthropic's Claude (version 3.5). The AI assistant helped in creating the core functionality, architecture, and documentation. Human oversight and modifications were applied to ensure proper functionality and security.

---

A web-based GPU monitoring system that provides real-time information about GPU usage across multiple servers. Built with FastAPI and modern web technologies, designed for IRAL lab at NTUA.

## Features

- Real-time GPU monitoring across multiple servers
- Memory usage visualization with progress bars
- Process and user tracking per GPU
- Performance state (P-State) monitoring
- Temperature monitoring
- Multi-server support through YAML configuration
- Clean, responsive Bootstrap interface

## Prerequisites

- Python 3.8+
- Apache2
- NVIDIA GPUs with nvidia-smi installed on monitored servers
- SSH access to monitored servers

## Quick Start for Development

1. Clone the repository and set up environment:
```bash
git clone https://github.com/filby89/simple-gpu-monitoring.git
cd gpu-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure servers:
```bash
cp config.sample.yaml config.yaml
# Edit config.yaml with your server details
```

3. Run development server:
```bash
python main.py
```


## License

MIT License

## Support

For support, please open an issue on the GitHub repository or contact IRAL lab maintainers.