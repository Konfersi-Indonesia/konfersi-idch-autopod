from datetime import datetime
import subprocess
import sys
from autopod.settings import config
from autopod.api import api_get_docker_ps, api_get_health, api_get_node_log, api_get_runner_log
from autopod.utils import cloud_init_generator, convert_to_dict, get_row_by_name, handle_json_resp
import requests as re
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
import time


idch_header = {
    "apikey": config.idch.token
}

def idch_get(path):
    url = os.path.join(config.idch.host, path.format(location=config.cluster.location))
    # print('GET ' + url)
    return handle_json_resp(re.get(url, headers=idch_header))

def idch_post(path, data):
    url = os.path.join(config.idch.host, path.format(location=config.cluster.location))
    # print('POST ' + url)
    return handle_json_resp(re.post(url, headers=idch_header, data=data))
    
    
def idch_delete(path, data=None):
    url = os.path.join(config.idch.host, path.format(location=config.cluster.location))
    # print('DELETE ' + url)
    handle_json_resp(re.delete(url, headers=idch_header, data=data))

def idch_delete_cluster():
    # Get the instances
    instances = idch_get_instances()

    # Run the deletion in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        # Submit delete tasks and wait for all of them to complete
        futures = [executor.submit(idch_delete_instance, row.get('uuid'), row.get('public_ipv4')) for _, row in instances.iterrows()]
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()  # Blocks until the task is done     
        
def idch_get_master_ip(ip_type="public"):
    df = idch_get_instances()  # Assume this returns a DataFrame with instance details
    if (df.empty): return
    
    filtered_df = df[df['name'].str.contains('_master_') & df['public_ipv4'].notna() & (df['public_ipv4'] != '')]
    first_row = filtered_df.head(1)
    
    return first_row[f'{ip_type}_ipv4'].item()

def idch_build_node(node_config, resource_config, role="master", environments = {}, id=1):
    with open(config.cluster.keypair.public, "r") as file:
        public_key = file.read()
        
    if (node_config.cloud_init.environments):
        environments.update(convert_to_dict(node_config.cloud_init.environments))

    environments["CLOUD_INIT_WORKDIR"] = "/home/" + config.cluster.username
    environments["NODE_ROLE"] = role
    environments["NODE_USER"] = config.cluster.username

    data = {
        "name": f"{config.cluster.name}_{role}_{id}",
        "os_name": node_config.os_name,
        "os_version": node_config.os_version,
        "disks": int(resource_config.storage),
        "vcpu": int(resource_config.cpu),
        "ram": int(resource_config.memory) * (2 ** 10),
        "username": config.cluster.username,
        "password": config.cluster.password,
        "public_key": public_key,
        "cloud_init": cloud_init_generator(node_config.cloud_init.files, node_config.cloud_init.runcmd, environments["CLOUD_INIT_WORKDIR"], environments=environments)
    }
    
    df = pd.DataFrame([data])
    print(df[["name", "os_name", "os_version", "disks", "vcpu", "ram"]].to_string(index=False, columns=False))
    

    return idch_post("v1/{location}/user-resource/vm", data)
    
def idch_delete_instance(uuid, ip_address):
    if (uuid):
        print("Deleting Container:", uuid)
        idch_delete("v1/{location}/user-resource/vm", data={
            "uuid": uuid,
        })
    
    if (ip_address):
        print("Deleting IP:", ip_address)
        idch_delete("v1/{location}/network/ip_addresses/" + ip_address)
        
def idch_get_instances():
    # Get the data from the API or external service
    vm_list = idch_get("v1/{location}/user-resource/vm/list")
    ip_addresses = idch_get("v1/{location}/network/ip_addresses")

    if (len(ip_addresses) == 0):
        return vm_list
    
    ip_addresses = ip_addresses.rename(columns={'address': 'public_ipv4', "uuid": "network_uuid"})
    
    if (len(vm_list) == 0):
        return ip_addresses
    

    # Step 1: Perform the join on uuid and assigned_to
    merged_df = pd.merge(vm_list, ip_addresses, left_on='uuid', right_on='assigned_to', how='inner')

    # Step 2: Filter rows where the 'name' column starts with config.cluster.name
    filtered_df = merged_df[merged_df['name'].str.startswith(config.cluster.name)]

    # Step 3: Create a new DataFrame to ensure we aren't working on a slice of the original DataFrame
    result = filtered_df[['uuid','network_uuid','name', 'private_ipv4', 'status', 'public_ipv4']].copy()

    # Step 4: Add the 'command' column using .loc to avoid SettingWithCopyWarning
    result.loc[:, 'command'] = result.apply(
        lambda row: (
            f"ssh -i {config.cluster.keypair.private} "
            "-o StrictHostKeyChecking=no "
            "-o UserKnownHostsFile=/dev/null "
            f"{config.cluster.username}@{row['public_ipv4']}"
        ),
        axis=1
    )


    return result

def idch_get_os():
    plain_oses = idch_get("v1/config/vm_images/plain_os")[['os_name', 'versions']].explode('versions')
    plain_oses['os_version'] = plain_oses['versions'].apply(lambda x: x['os_version'])
    del plain_oses['versions']
    return plain_oses 

def idch_get_app_catalog():
    app_catalogs = idch_get("v1/config/vm_images/app_catalog")[['os_name', 'versions']].explode('versions')
    app_catalogs['os_version'] = app_catalogs['versions'].apply(lambda x: x['os_version'])
    del app_catalogs['versions']
    return app_catalogs 

def idch_build_master_node(init=False):
    print("Building master node...")
    if (init):
        return idch_build_node(config.master, config.master.resources.init)
    else:
        return idch_build_node(config.master, config.master.resources)

def idch_build_worker_node():
    f"Building {config.worker.nodes} worker nodes..."
    master_node_ip = idch_get_master_ip(ip_type="private")

    def runner(id, master_node_ip):
        idch_build_node(config.worker, config.worker.resources, role="worker", id=id, environments={
            "MASTER_NODE_IP": master_node_ip
        })
    
    with ThreadPoolExecutor() as executor:
        # Submit delete tasks and wait for all of them to complete
        futures = [executor.submit(runner, id, master_node_ip) for id in range(1, int(config.worker.nodes) + 1)]
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()  # Blocks until the task is done   
    
    return 'Build complete please do "autopod vm ls" to check spawned vms'
    
def idch_stop_node():
    pass

def idch_modify_node():
    pass
    
def idch_start_cluster():
    # if available -> sync
    # else build master
    # init master
    # stop master
    # modify master
    # sync
    pass
    
def idch_sync_cluster():
    pass
    
def idch_stop_cluster():
    pass

def idch_open_shell(argv_no=3):
    name = sys.argv[argv_no]
    
    df = idch_get_instances()
    if (len(df) == 0): return

    ssh_command = get_row_by_name(df, name)['command']
    
    try:        
        # Use subprocess to run the command interactively
        subprocess.run(
            ssh_command,
            shell=True,
            check=True
        )
        
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        
    return "Done."
        
def idch_node_status(ip):
    health = api_get_health(ip)
    log = pd.DataFrame()
    done = pd.DataFrame()
    has_error = False
    if health:
        log, done, has_error = api_get_runner_log(ip)
    
    return health, log, done, has_error

def idch_node_status_print(argv_no=3):
    name = sys.argv[argv_no]
    
    df = idch_get_instances()
    if (len(df) == 0): return
    
    ip = get_row_by_name(df, name)['public_ipv4']
    df = pd.DataFrame({'ip': [ip]})
    
    health, log, done, has_error = idch_node_status(ip)

    messages = []
    messages.append("Server Status: " + "HEALTHY" if health else "UNHEALTHY")
    
    if health:
        if not done.empty:
            messages.append("Script Status: " + ("FAILED" if has_error else "DONE"))
            messages.append(f"{done[['status', 'logfile']]}")
        else: 
            if not log.empty:
                messages.append(f"Script Status: {log.tail(1)['status'].item().upper()}")
                messages.append(f"\nInitialize Script Summary:")
                messages.append(f"{log}")
            else:
                messages.append("Script Status: WAITING")
    
    return "\n".join(messages)

# Assuming you have your instances DataFrame ready
def idch_healthcheck_instance():
    instances = idch_get_instances()  # Assume this returns a DataFrame with instance details
    if (instances.empty): return
    
    healthy_set = {}
    logs_count = {}

    while len(healthy_set) != len(instances):  # Corrected condition
        
        for ip in instances['public_ipv4']:
            ip = str(ip)
            if ip in healthy_set:  # Corrected to check if IP is in healthy_set
                continue
            try:
                health, log, done, has_error = idch_node_status(ip)
            except:
                continue
            
            if health and not done.empty:
                healthy_set[ip] = not has_error
                print(instances[instances['public_ipv4'] == ip]['name'].values[0], "is completed", "with error" if has_error else "and healthy")
            
            if (ip not in logs_count.keys()): logs_count[ip] = 0
            new_logs_count = len(log) - logs_count[ip]
            
            if new_logs_count > 0:
                new_logs = log.iloc[logs_count[ip]:]  # Get the new logs
                new_logs.insert(1, "ip", ip)
                new_logs = new_logs.fillna("")
                
                print(new_logs.to_string(header=len(logs_count) == 1, index=False))
                logs_count[ip] += new_logs_count
    
        time.sleep(1)
        instances = idch_get_instances()  # Assume this returns a DataFrame with instance details
        
    return "All services are healthy"

def idch_get_cluster_services():
    ip = idch_get_master_ip()
    
    return pd.DataFrame([{
        "service": "grafana",
        "address": f"http://{ip}:3000"
    },{
        "service":"portainer",
        "address":f"https://{ip}:9443"
    },{
        "service":"mpi-server",
        "address":f"http://{ip}:8822/?folder=/home/mpi/workspace"
    }])

def idch_get_node_log(argv_no=3):
    name = sys.argv[argv_no]
    log = sys.argv[argv_no + 1]
    n = 10
    if len(sys.argv) > argv_no + 2:
        n = sys.argv[argv_no + 2]
        
    df = idch_get_instances()
    if (len(df) == 0): return

    ip = get_row_by_name(df, name)['public_ipv4']
    return api_get_node_log(ip, log, n)