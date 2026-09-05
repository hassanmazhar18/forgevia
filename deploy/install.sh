#!/usr/bin/env bash
# Forgevia one-shot installer for Ubuntu 22.04/24.04 (Google Compute Engine).
# Usage: sudo bash install.sh yourdomain.com you@email.com
set -euo pipefail
DOMAIN="${1:?domain required}"; EMAIL="${2:?email required}"
APP=/opt/forgevia
apt-get update -y && apt-get install -y python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx sudo git unzip
id -u fvrun &>/dev/null || useradd -r -M -s /usr/sbin/nologin fvrun
id -u forgevia &>/dev/null || useradd -r -m -s /bin/bash forgevia
mkdir -p $APP && cp -r "$(dirname "$0")/.." $APP/src 2>/dev/null || true
cd $APP/src
python3 -m venv $APP/venv && $APP/venv/bin/pip install -q --upgrade pip
$APP/venv/bin/pip install -q fastapi uvicorn beautifulsoup4 httpx python-multipart lxml
$APP/venv/bin/pip install -q playwright && $APP/venv/bin/python -m playwright install --with-deps chromium || true
echo "forgevia ALL=(fvrun) NOPASSWD: ALL" > /etc/sudoers.d/forgevia && chmod 440 /etc/sudoers.d/forgevia
chown -R forgevia:forgevia $APP; chmod 711 $APP $APP/src; chmod 700 $APP/src/projects 2>/dev/null || true
cat > /etc/systemd/system/forgevia.service <<UNIT
[Unit]
Description=Forgevia
After=network.target
[Service]
User=forgevia
WorkingDirectory=$APP/src
Environment=FV_PUBLIC_URL=https://$DOMAIN
ExecStart=$APP/venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload && systemctl enable --now forgevia
cat > /etc/nginx/sites-available/forgevia <<NG
server {
  listen 80; server_name $DOMAIN www.$DOMAIN;
  client_max_body_size 100m;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_http_version 1.1; proxy_set_header Upgrade \$http_upgrade; proxy_set_header Connection "upgrade";
    proxy_read_timeout 300;
  }
}
NG
ln -sf /etc/nginx/sites-available/forgevia /etc/nginx/sites-enabled/forgevia; rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect || echo "!! certbot failed — is DNS pointing here yet? Re-run: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "=============================================="
echo " Forgevia is live: https://$DOMAIN"
echo " status : systemctl status forgevia"
echo " logs   : journalctl -u forgevia -f"
echo " update : cd $APP/src && git pull && systemctl restart forgevia"
echo "=============================================="
