#!/bin/bash

PORTAINER_ADMIN_PASSWORD=${PORTAINER_ADMIN_PASSWORD:-konfersiindonesia}
export SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

mkdir -p ${SCRIPT_PATH}/portainer_data
echo -n "${PORTAINER_ADMIN_PASSWORD}" > ${SCRIPT_PATH}/portainer_data/passwd

docker stack deploy -c ${SCRIPT_PATH}/4-portainer-agent-stack.yml portainer

