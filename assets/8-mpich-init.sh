#!/bin/bash

SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-'/home/ubuntu'}" 
export MPICH_BASE_IMAGE=${MPICH_BASE_IMAGE:-'alfianisnan26/konfersi-mpi:latest'}
export MPICH_PASSWORD=${MPICH_PASSWORD:-'konfersiindonesia'}
export MPICH_WORKER_CPU_LIMIT=${MPICH_WORKER_CPU_LIMIT:-15}
export MPICH_WORKER_MEMORY_LIMIT=${MPICH_WORKER_MEMORY_LIMIT:-2500}
export MASTER_NODE_IP=${MASTER_NODE_IP:-$(/sbin/ip -o -4 addr list ens3 | awk '{print $4}' | cut -d/ -f1)}

docker stack deploy -c ${SCRIPT_PATH}/8-mpich-agent-stack.yaml mpich
