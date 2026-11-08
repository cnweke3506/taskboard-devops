#!/bin/bash
# Runs once on first boot: install Docker and start the app container.
set -euxo pipefail
dnf install -y docker
systemctl enable --now docker
mkdir -p /opt/taskboard/data
chown 10001 /opt/taskboard/data
docker run -d --name taskboard --restart unless-stopped \
  -p 8000:8000 -v /opt/taskboard/data:/data ${image}
