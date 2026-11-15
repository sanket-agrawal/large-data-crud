#!/usr/bin/env bash
# ==============================================================================
# Hostinger VPS (KVM 2) Deployment Script
# Universal Data Search & Management Engine (2M+ Records)
# ==============================================================================

set -e

echo "=========================================================="
echo " Starting Deployment on Hostinger VPS..."
echo "=========================================================="

# 1. Update system packages
echo "[1/6] Updating system packages and installing prerequisites..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    rsync \
    ufw

# 2. Install Docker & Docker Compose if not present
echo "[2/6] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker Engine..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo systemctl enable docker
    sudo systemctl start docker
    rm -f get-docker.sh
fi

if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    sudo apt-get install -y docker-compose-plugin
fi

# 3. Configure Firewall (UFW)
echo "[3/6] Configuring firewall rules (SSH, HTTP, HTTPS)..."
sudo ufw allow 22/tcp || true
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw --force enable || true

# 4. Check for .env file
echo "[4/6] Verifying environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "Please edit .env to set your desired domain and passwords if needed."
    else
        cat << 'EOF' > .env
DOMAIN_NAME=vehicle.sanketagrawal.com
SSL_EMAIL=dayamapratik43@gmail.com
POSTGRES_DB=auth_db
POSTGRES_USER=appuser
POSTGRES_PASSWORD=SecurePostgresPass2026!
ADMIN_EMAIL=dayamapratik43@gmail.com
ADMIN_PASSWORD=AdminMasterPass2026!
DEFAULT_MASTER_PASSWORD=Pass@123456
DUCKDB_PATH=/app/data/records.duckdb
EOF
    fi
fi

# 5. Ensure data directory exists
mkdir -p data

if [ ! -f "data/records.duckdb" ]; then
    echo "=========================================================="
    echo " ATTENTION: 'data/records.duckdb' not found!"
    echo " Please upload your ~814MB records.duckdb to the ./data folder:"
    echo "   scp -C /path/to/records.duckdb root@<VPS_IP>:$(pwd)/data/records.duckdb"
    echo "=========================================================="
fi

# 6. Launch Docker Compose (PostgreSQL + App + Caddy HTTPS)
echo "[5/6] Building and launching containers..."
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --build

echo "[6/6] Checking container health..."
docker compose -f docker-compose.prod.yml ps

echo "=========================================================="
echo " Deployment Complete!"
echo " Web Application URL: https://$(grep DOMAIN_NAME .env | cut -d '=' -f2)"
echo " Admin Email:         $(grep ADMIN_EMAIL .env | cut -d '=' -f2)"
echo " Master Password:     $(grep DEFAULT_MASTER_PASSWORD .env | cut -d '=' -f2)"
echo "=========================================================="

