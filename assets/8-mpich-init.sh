#!/bin/bash
SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

sudo mkdir -p ${SCRIPT_PATH}/nfs-data/mpich

sudo docker stack deploy -c ${SCRIPT_PATH}/8-mpich-agent-stack.yaml mpich

CONTAINER_NAME="mpich_mpi_master"
RETRY_DELAY=5
GDRIVE_CREDENTIAL_FILE="konfersi-service-account-gdrive.json"
GDRIVE_ROOT_FOLDER_ID="1-fxBjSiB0q3qYIic2r_dGomP88xgn4Sj"

while true; do
    # Check if the container is running
    CONTAINER_ID=$(sudo docker ps --filter "name=$CONTAINER_NAME" --filter "status=running" --format "{{.ID}}")
    
    if [[ -n "$CONTAINER_ID" ]]; then
        echo "Container '$CONTAINER_NAME' is running. Proceeding..."
        break
    else
        # Get the current time and calculate the elapsed time
        CURRENT_TIME=$(date +%s)
        ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

        if [[ $ELAPSED_TIME -ge $TIMEOUT ]]; then
            echo "Timeout reached after 15 minutes. Exiting..."
            exit 1  # Exit with error code
        fi

        echo "Waiting for the container '$CONTAINER_NAME' to start..."
        sleep $RETRY_DELAY
    fi
done

echo "Installing rclone"
sudo docker exec ${CONTAINER_ID} sh -c "sudo apt install rclone -y"

echo "Copying files"
sudo docker cp ${SCRIPT_PATH}/${GDRIVE_CREDENTIAL_FILE} ${CONTAINER_ID}:/home/mpi/credential.json

# Define file content
FILE_CONTENT="[gdrive]
type = drive
scope = drive
root_folder_id = ${GDRIVE_ROOT_FOLDER_ID}
service_account_file = /home/mpi/credential.json"

sudo docker exec ${CONTAINER_ID} sh -c "mkdir -p ~/.config/rclone"
sudo docker exec ${CONTAINER_ID} sh -c "echo \"${FILE_CONTENT}\" > ~/.config/rclone/rclone.conf"

# Copy all content to workspace
sudo docker exec ${CONTAINER_ID} sh -c "rclone copy gdrive: ~/workspace --log-file /home/mpi/workspace/copy.log --log-level DEBUG --progress"