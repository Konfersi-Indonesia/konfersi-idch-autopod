SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

mkdir -p ${SCRIPT_PATH}/nfs-data/mpich

docker stack deploy -c ${SCRIPT_PATH}/8-mpich-agent-stack.yaml mpich
#!/bin/bash

CONTAINER_NAME="mpich_mpi_master"
RETRY_DELAY=5
GDRIVE_CREDENTIAL_FILE="konfersi-service-account-gdrive.json"
GDRIVE_ROOT_FOLDER_ID="1-fxBjSiB0q3qYIic2r_dGomP88xgn4Sj"

while true; do
    # Check if the container is running
    CONTAINER_ID=$(docker ps --filter "name=$CONTAINER_NAME" --filter "status=running" --format "{{.ID}}")
    
    if [[ -n "$CONTAINER_ID" ]]; then
        echo "Container '$CONTAINER_NAME' is running. Proceeding..."
        break
    else
        echo "Waiting for the container '$CONTAINER_NAME' to start..."
        sleep $RETRY_DELAY
    fi
done

echo "Installing rclone"
docker exec ${CONTAINER_ID} sh -c "sudo apt install rclone -y"

echo "Copying files"
docker cp ${SCRIPT_PATH}/${GDRIVE_CREDENTIAL_FILE} ${CONTAINER_ID}:/home/mpi/credential.json

# Define file content
FILE_CONTENT="[gdrive]
type = drive
scope = drive
root_folder_id = ${GDRIVE_ROOT_FOLDER_ID}
service_account_file = /home/mpi/credential.json"

docker exec ${CONTAINER_ID} sh -c "mkdir -p ~/.config/rclone"
docker exec ${CONTAINER_ID} sh -c "echo \"${FILE_CONTENT}\" > ~/.config/rclone/rclone.conf"

# Copy all content to workspace
docker exec ${CONTAINER_ID} sh -c "rclone copy gdrive: ~/workspace --log-file /home/mpi/workspace/copy.log --log-level DEBUG --progress"