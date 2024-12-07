#!/bin/bash
sudo apt install apache2-utils -y

PORTAINER_ADMIN_PASSWORD="${PORTAINER_ADMIN_PASSWORD:-konfersiindonesia}" 
SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

mkdir -p portainer_data

echo -n $PORTAINER_ADMIN_PASSWORD > portainer_data/portainer_password

docker stack deploy -c ${SCRIPT_PATH}/4-portainer-agent-stack.yml portainer

