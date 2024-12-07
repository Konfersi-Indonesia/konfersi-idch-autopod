SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 
export GRAFANA_USERNAME="${GRAFANA_USERNAME:-konfersiadmin}" 
export GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-konfersiindonesia}" 

sudo docker stack deploy -c ${SCRIPT_PATH}/5-grafana-agent-stack.yml grafana