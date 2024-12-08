#!/bin/bash

sudo apt install apache2-utils -y

PORTAINER_ADMIN_PASSWORD=${PORTAINER_ADMIN_PASSWORD:-konfersiindonesia}

export SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 
export PORTAINER_ADMIN_PASSWORD_BCRYPT=$(htpasswd -nb -B admin "${PORTAINER_ADMIN_PASSWORD}" | cut -d ":" -f 2)

docker stack deploy -c ${SCRIPT_PATH}/4-portainer-agent-stack.yml portainer

mkdir -p ${SCRIPT_PATH}/portainer_data
echo -n "${PORTAINER_ADMIN_PASSWORD}" > ${SCRIPT_PATH}/portainer_data/passwd