#!/bin/bash

SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

SERVICE_NAME=${MPICH_MASTER_SERVICE_NAME:-mpich_mpi_master}
RETRY_DELAY=${RETRY_DELAY:-5}
GDRIVE_CREDENTIAL_FILE=${GDRIVE_CREDENTIAL_FILE:-credential.json}
TIMEOUT=${RETRY_DELAY:-15}
INIT_TRANSFER_CONFIG_FILE=${INIT_TRANSFER_CONFIG_FILE:-transfer-config.yaml}

if [ -z "$GDRIVE_ROOT_FOLDER_ID" ]; then
  echo "Error: GDRIVE_ROOT_FOLDER_ID is not set or is empty."
  return 1
fi

# Your script logic continues here
echo "GDRIVE_ROOT_FOLDER_ID is set to: $GDRIVE_ROOT_FOLDER_ID"

while true; do
    # Check if the container is running
    CONTAINER_ID=$(docker ps --filter "name=$SERVICE_NAME" --filter "status=running" --format "{{.ID}}")
    
    if [[ -n "$CONTAINER_ID" ]]; then
        echo "Container '$SERVICE_NAME' is running. Proceeding..."
        break
    else
        # Get the current time and calculate the elapsed time
        CURRENT_TIME=$(date +%s)
        ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

        if [[ $ELAPSED_TIME -ge $TIMEOUT ]]; then
            echo "Timeout reached after 15 minutes. Exiting..."
            return 1  # Exit with error code
        fi

        echo "Waiting for the container '$SERVICE_NAME' to start..."
        sleep $RETRY_DELAY
    fi
done

echo "WRF File adjustment init"
docker exec ${CONTAINER_ID} sh -c "cp -r /home/mpi/wps /home/mpi/workspace"
docker exec ${CONTAINER_ID} sh -c "cp -r /home/mpi/wrf /home/mpi/workspace"
docker exec ${CONTAINER_ID} sh -c "rm -r /home/mpi/wps /home/mpi/wrf /home/mpi/wrf_installer"

echo "Installing rclone"
docker exec ${CONTAINER_ID} sh -c "sudo apt install rclone -y"

echo "Copying files"
docker cp ${SCRIPT_PATH}/${GDRIVE_CREDENTIAL_FILE} ${CONTAINER_ID}:/home/mpi/credential.json
docker cp ${SCRIPT_PATH}/${INIT_TRANSFER_CONFIG_FILE} ${CONTAINER_ID}:/home/mpi/workspace/transfer-config.yaml

# Define file content
FILE_CONTENT="[gdrive]
type = drive
scope = drive
root_folder_id = ${GDRIVE_ROOT_FOLDER_ID}
service_account_file = /home/mpi/credential.json"

echo "Execute transfer files"
docker exec ${CONTAINER_ID} sh -c "mkdir -p ~/.config/rclone"
docker exec ${CONTAINER_ID} sh -c "echo \"${FILE_CONTENT}\" > ~/.config/rclone/rclone.conf"