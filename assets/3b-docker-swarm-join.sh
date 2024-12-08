#!/bin/bash

# Check if MASTER_NODE_IP environment variable is set
if [ -z "$MASTER_NODE_IP" ]; then
    echo "Error: MASTER_NODE_IP environment variable is not set."
    exit 1
fi

# URL of the master node's /docker/swarm/token endpoint
MASTER_NODE="http://$MASTER_NODE_IP:8181"  # Use the environment variable for the master node IP

# Obtain the token from the master node
TOKEN=$(curl -s "$MASTER_NODE/docker/swarm/token" | jq -r '.token')

# Check if the token is not empty
if [ -z "$TOKEN" ]; then
    echo "Error: Token not received from master node."
    exit 1
fi

# Join the swarm using the obtained token
sudo docker swarm join --token "$TOKEN" "$MASTER_NODE_IP:2377"  # Default Docker Swarm port is 2377

if [ $? -eq 0 ]; then
    echo "Successfully joined the Docker swarm."
else
    echo "Failed to join the Docker swarm."
    exit 1
fi
