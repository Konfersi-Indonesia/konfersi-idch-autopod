#!/bin/bash
PORTAINER_ADMIN_PASSWORD="${PORTAINER_ADMIN_PASSWORD:-konfersiindonesia}" 
SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 
export PORTAINER_ADMIN_PASSWORD_BCRYPT=$(htpasswd -nb -B admin "${PORTAINER_ADMIN_PASSWORD}" | cut -d ":" -f 2)

docker stack deploy -c ${SCRIPT_PATH}/4-portainer-agent-stack.yml portainer

