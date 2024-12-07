ip4=$(/sbin/ip -o -4 addr list ens3 | 
awk '{print $4}' | cut -d/ -f1)

docker run -itd --privileged \
  --restart unless-stopped \
  -e SHARED_DIRECTORY=/data \
  -v ~/nfs-data:/data \
  -p 2049:2049 \
  --name nfs-server \
  itsthenetwork/nfs-server-alpine:12

mkdir -p /home/ubuntu/nfs-data/mpich