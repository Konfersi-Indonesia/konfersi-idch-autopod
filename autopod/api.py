import requests as re
import json
import pandas as pd

def api_get_health(ip):
    try:
        resp = re.get("http://" + ip + ":8181/health", timeout=5)
        if (resp.status_code != 200):
            return False
    except re.ConnectTimeout:
        return False
    
    return True

def api_get_runner_log(ip):    
    resp = re.get("http://" + ip + ":8181/logs/init-runner-executor.log")
    logs = []
    for item in resp.text.split("\n"):
        try:
            logs.append(json.loads(item))
        except:
            pass
        
    df = pd.DataFrame(logs)
    summary = df[['status', 'script', 'script_status', 'log_file']]
        
    done_data = df[df['status'] == 'done']
    done_summary = pd.DataFrame()
    has_error = False
    
    if (not done_data.empty):
        done_summary = pd.DataFrame(done_data['result'].explode().to_list())
        has_error = int(done_data['script_failed'].iloc[0]) > 0
        
    return summary, done_summary, has_error

def api_get_node_log(ip, log, n=10):
    resp = re.get("http://" + ip + ":8181/logs/" + log + f"?n={n}")
    return resp.text

def api_get_docker_ps(ip):
    resp = re.get("http://" + ip + ":8181/docker/ps")
    return resp.text

def api_get_docker_swarm_token(ip):
    resp = re.get("http://" + ip + ":8181/docker/swarm/token")
    return resp.text