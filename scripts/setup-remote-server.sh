#!/bin/bash

# Remote Server Setup Script for Qshing Server Deployment
# Run this script on the remote server (134.185.102.63) before first deployment

set -e

echo "=== Qshing Server - Remote Server Setup ==="

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

# Install other dependencies
echo "Installing additional dependencies..."
sudo apt install -y curl jq htop git

# Create application directory
echo "Creating application directory..."
mkdir -p ~/qshing-server
cd ~/qshing-server

# Create basic nginx configuration for reverse proxy (optional)
echo "Creating nginx configuration..."
sudo apt install -y nginx

cat > ~/qshing-server/nginx.conf << 'EOF'
server {
    listen 80;
    server_name 134.185.102.63;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8080/health;
        access_log off;
    }
}
EOF

# Setup nginx configuration
sudo cp ~/qshing-server/nginx.conf /etc/nginx/sites-available/qshing-server
sudo ln -sf /etc/nginx/sites-available/qshing-server /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Setup firewall
echo "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable

# Setup log rotation for Docker
echo "Setting up log rotation..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# Restart Docker to apply log configuration
sudo systemctl restart docker

# Create systemd service for automatic startup
echo "Creating systemd service..."
sudo tee /etc/systemd/system/qshing-server.service > /dev/null <<EOF
[Unit]
Description=Qshing Server
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/qshing-server
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=$USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable qshing-server.service

# Setup monitoring script
echo "Creating monitoring script..."
cat > ~/qshing-server/monitor.sh << 'EOF'
#!/bin/bash

# Simple monitoring script for Qshing Server
echo "=== Qshing Server Status ==="
echo "Date: $(date)"
echo ""

echo "=== Docker Containers ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== System Resources ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h /
echo ""
echo "CPU Load:"
uptime
echo ""

echo "=== Application Logs (last 10 lines) ==="
cd /home/$USER/qshing-server
docker-compose -f docker-compose.prod.yml logs --tail=10
EOF

chmod +x ~/qshing-server/monitor.sh

# Setup cron job for health monitoring
echo "Setting up health monitoring..."
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /home/$USER/qshing-server && ./monitor.sh >> /var/log/qshing-monitor.log 2>&1") | crontab -

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Log out and log back in for Docker group changes to take effect"
echo "2. Configure GitHub Secrets with the following values:"
echo "   - REMOTE_USER: $USER"
echo "   - REMOTE_SSH_KEY: (your private SSH key)"
echo "   - OCI_BUCKET_URL: (your AI model bucket URL)"
echo "   - Database connection secrets (MONGODB_*, POSTGRES_*, REDIS_*)"
echo ""
echo "3. Start nginx:"
echo "   sudo systemctl start nginx"
echo "   sudo systemctl enable nginx"
echo ""
echo "4. Run monitor script to check status:"
echo "   ~/qshing-server/monitor.sh"
echo ""
echo "Server is ready for deployment!" 