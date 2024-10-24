# GPU Monitor

## ⚠️ Development Disclaimer
This project was primarily developed with the assistance of Anthropic's Claude (version 3.5). The AI assistant helped in creating the core functionality, architecture, and documentation. Human oversight and modifications were applied to ensure proper functionality and security.

---

A web-based GPU monitoring system that provides real-time information about GPU usage across multiple servers. Built with FastAPI and modern web technologies.

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
- Apache2 (for production deployment)
- NVIDIA GPUs with nvidia-smi installed on monitored servers
- SSH access to monitored servers

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gpu-monitor.git
cd gpu-monitor
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
cp config.sample.yaml config.yaml
```

5. Edit `config.yaml` with your server details:
```yaml
servers:
  - name: "GPU Server 1"
    hostname: "your-server-1.domain.com"
    port: 22
  - name: "GPU Server 2"
    hostname: "your-server-2.domain.com"
    port: 22
```

6. Run the development server:
```bash
python main.py
```

7. Access the monitor at `http://localhost:8000`

## Production Deployment with Apache

1. Install required packages:
```bash
sudo apt-get update
sudo apt-get install apache2 apache2-dev python3-dev
sudo apt-get install libapache2-mod-wsgi-py3
```

2. Create project directory:
```bash
sudo mkdir /var/www/gpu_monitor
sudo chown -R $USER:$USER /var/www/gpu_monitor
```

3. Set up virtual environment in production:
```bash
cd /var/www/gpu_monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Configure Apache:
```bash
sudo nano /etc/apache2/sites-available/gpu_monitor.conf
```

Add the following configuration:
```apache
<VirtualHost *:80>
    ServerName your_domain.com
    ServerAdmin webmaster@your_domain.com

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    Alias /static /var/www/gpu_monitor/static
    <Directory /var/www/gpu_monitor/static>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/gpu_monitor_error.log
    CustomLog ${APACHE_LOG_DIR}/gpu_monitor_access.log combined
</VirtualHost>
```

5. Enable required Apache modules:
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2ensite gpu_monitor
sudo systemctl restart apache2
```

6. Create systemd service:
```bash
sudo nano /etc/systemd/system/gpu_monitor.service
```

Add the following content:
```ini
[Unit]
Description=GPU Monitor FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/gpu_monitor
Environment="PATH=/var/www/gpu_monitor/venv/bin"
ExecStart=/var/www/gpu_monitor/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

[Install]
WantedBy=multi-user.target
```

7. Start and enable the service:
```bash
sudo systemctl start gpu_monitor
sudo systemctl enable gpu_monitor
```

## Configuration

The `config.yaml` file supports the following options:

```yaml
servers:
  - name: "Server Name"    # Display name for the server
    hostname: "hostname"   # Server hostname or IP
    port: 22              # SSH port number
```

## Security Considerations

1. SSH Access:
   - Use SSH keys instead of passwords
   - Create a dedicated user for monitoring
   - Restrict SSH access to specific IPs if possible

2. Web Access:
   - Set up SSL/TLS using Let's Encrypt
   - Implement authentication if needed
   - Keep all packages updated

3. File Permissions:
   - Secure config.yaml permissions:
     ```bash
     sudo chmod 600 /var/www/gpu_monitor/config.yaml
     sudo chown www-data:www-data /var/www/gpu_monitor/config.yaml
     ```

## Troubleshooting

1. Check Apache logs:
```bash
sudo tail -f /var/log/apache2/gpu_monitor_error.log
```

2. Check application logs:
```bash
sudo journalctl -u gpu_monitor
```

3. Common issues:
   - SSH connection failures: Check SSH keys and permissions
   - "No such file": Check paths in Apache configuration
   - "Permission denied": Check file permissions

## Development

1. Running tests:
```bash
pytest tests/
```

2. Code formatting:
```bash
black .
```

3. Linting:
```bash
flake8 .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI development team
- Bootstrap team
- NVIDIA for nvidia-smi

## Support

For support, please open an issue on the GitHub repository or contact the maintainers.