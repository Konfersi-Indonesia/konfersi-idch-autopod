#!/bin/bash
PORTAINER_ADMIN_PASSWORD="${PORTAINER_ADMIN_PASSWORD:-konfersiindonesia}" 
SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

sudo docker stack deploy -c ${SCRIPT_PATH}/4-portainer-agent-stack.yml portainer

