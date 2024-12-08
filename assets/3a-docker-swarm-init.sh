#!/bin/bash

# Check if MASTER_NODE_IP is already set and non-empty
export MASTER_NODE_IP=${MASTER_NODE_IP:-$(/sbin/ip -o -4 addr list ens3 | awk '{print $4}' | cut -d/ -f1)}

docker swarm init --advertise-addr ${MASTER_NODE_IP}