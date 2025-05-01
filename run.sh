#!/bin/bash

cd /home/yair/projects/fastapi-webhook
# cd /home/yair/webhook

source env/bin/activate

exec fastapi run  ./app/main.py --port 8001


# sudo nano /etc/systemd/system/fastapi-webhook.service

# [Unit]
# Description=FastAPI app webhook
# After=network.target

# [Service]
# User=yair
# WorkingDirectory=/home/yair/projects/fastapi-webhook
# ExecStart=/home/yair/projects/fastapi-webhook/start.sh
# Restart=always
# RestartSec=5
# Environment=PYTHONUNBUFFERED=1

# [Install]
# WantedBy=multi-user.target

