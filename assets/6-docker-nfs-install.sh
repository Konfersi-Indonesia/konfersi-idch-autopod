SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 

sudo docker run -itd --privileged \
  --restart unless-stopped \
  -e SHARED_DIRECTORY=/data \
  -v ${SCRIPT_PATH}/nfs-data:/data \
  -p 2049:2049 \
  --name nfs-server \
  itsthenetwork/nfs-server-alpine:12