###################### Init Config and Dependency ######################

from yaml import safe_load
from types import SimpleNamespace
import requests as re
import pandas as pd
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import json
from tqdm import tqdm
import re as regex
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import time


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

def substitute_env_variables(yaml_content):
    """Substitute environment variables in the YAML content."""
    # Regular expression to match ${VAR} or $VAR
    pattern = regex.compile(r'\${(.*?)}|\$(\w+)')
    
    def replace(match):
        # Get the environment variable name from the match
        env_var = match.group(1) or match.group(2)
        # Return the value of the environment variable, or the original text if not found
        res = os.environ.get(env_var, match.group(0))
        return res
    
    # Replace environment variable placeholders with actual values
    return pattern.sub(replace, yaml_content)

def map_to_namespace(mapping):
    """
    Convert a mapping (like a dictionary or map object) into a nested namespace.
    """
    if isinstance(mapping, dict):  # If the object is a dictionary
        return SimpleNamespace(**{key: map_to_namespace(value) for key, value in mapping.items()})
    elif isinstance(mapping, (list, tuple)):  # For lists or tuples, apply recursively
        return [map_to_namespace(item) for item in mapping]
    else:  # Base case: return as is
        return mapping

def load_config(path):
    """Load and parse a YAML config file with environment variable substitution."""
    # Load environment variables from a .env file if available
    load_dotenv()

    with open(path, 'r') as file:
        # Read the file content
        yaml_content = file.read()
        # Substitute environment variables in the content
        yaml_content = substitute_env_variables(yaml_content)
        # Now parse the YAML content after substitution
        return safe_load(yaml_content)


def generate_ssh_key_pair(key_name="id_rsa", key_size=2048):
    """
    Generate an RSA SSH key pair and save them as files.

    Args:
        key_name (str): The base name of the key files (default is 'id_rsa').
        key_size (int): The size of the RSA key in bits (default is 2048).
    """
    # Generate the private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    # Serialize and save the private key
    private_key_path = f"{key_name}"
    with open(private_key_path, "wb") as priv_file:
        priv_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )
    print(f"Private key saved to: {private_key_path}")

    # Generate the public key
    public_key = private_key.public_key()

    # Serialize and save the public key in OpenSSH format
    public_key_path = f"{key_name}.pub"
    with open(public_key_path, "wb") as pub_file:
        pub_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            )
        )

    fix_private_key_permissions(public_key_path)
    print(f"Public key saved to: {public_key_path}")
    return public_key_path

def build_write_file_cloud(file, permissions = "0755", encoding = "b64", path="/home/ubuntu", ):
    target_path = os.path.join(path, os.path.basename(file))
    
    with open(file, "rb") as file:  # Always read as binary
        content = file.read()
        encoded_content = base64.b64encode(content).decode('utf-8')  # Base64 encode
        
    # Add to write_files
    return {
        "path": target_path,
        "content": encoded_content,
        "permissions": permissions,  # Ensuring the script is executable
        "encoding": encoding
    }

def cloud_init_writer(path="/home/ubuntu", files=[], bash_files=[], environments={}):
    write_files = []
    runcmd = []
    
    # Write files section
    for file in files:
        write_files.append(build_write_file_cloud(file, path=path))
    
    # Environment variables section
    for key, value in environments.items():
        runcmd.append(f"export {key}='{value}'")
    
    # Bash files section
    for bash_file in bash_files:
        # Get the filename from the full file path
        filename = os.path.basename(bash_file)
        target_path = os.path.join(path, filename)
        log_file = f"/var/log/{filename}.log"  # Log file to store output
        
        # Add to runcmd
        runcmd.extend([
            f"echo 'Running script: {filename}' >> /var/log/cloud-init.log",
            f"chown ubuntu:ubuntu {target_path}",
            f"chmod +x {target_path}",
            # Run the script and capture output (both stdout and stderr) to log file
            f"{target_path} >> {log_file} 2>&1",  # Redirect both stdout and stderr
            f"echo 'Script {filename} execution complete' >> {log_file}"
        ])
    
    return {
        "write_files": write_files,
        "runcmd": runcmd
    }

def cloud_init_generator(files, runcmd, path="/home/ubuntu", environments = {}):
    if not isinstance(files, list):
        folder_path = files
        files = [os.path.join(files, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    return json.dumps(cloud_init_writer(path, files, runcmd, environments=environments))

config = map_to_namespace(load_config("config.yaml"))

idch_header = {
    "apikey": config.idch.token
}

def idch_get(path):
    url = os.path.join(config.idch.host, path.format(location=config.cluster.location))
    print('GET ' + url)
    return pd.DataFrame(re.get(url, headers=idch_header).json())

def idch_post(path, data):
    url = os.path.join(config.idch.host, path.format(location=config.cluster.location))
    print('POST ' + url, data)
    res = re.post(url, headers=idch_header, data=data).json()
    return pd.DataFrame(res)
    
def idch_delete(path, data=None):
    url = os.path.join(config.idch.host, path.format(location=config.cluster.location))
    print('DELETE ' + url)
    print(re.delete(url, headers=idch_header, data=data).json())

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
        print(vm_list)
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

def convert_to_dict(key_value_list):
    result = {}
    for item in key_value_list:
        key, value = item.split("=", 1)  # Split at the first '=' character
        result[key] = value
    return result

def idch_build_node(node_config, resource_config, role="master", environments = {}):
    with open(config.cluster.keypair.public, "r") as file:
        public_key = file.read()
        
    if (node_config.cloud_init.environments):
        environments.update(convert_to_dict(node_config.cloud_init.environments))

    environments["CLOUD_INIT_WORKDIR"] = "/home/" + config.cluster.username
    environments["NODE_ROLE"] = role
    environments["NODE_USER"] = config.cluster.username


    data = {
        "name": config.cluster.name + "_master",
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

    return idch_post("v1/{location}/user-resource/vm", data)

# Assuming you have your instances DataFrame ready
def idch_healthcheck_instance():
    instances = idch_get_instances()  # Assume this returns a DataFrame with instance details
    health_set = {}
    count = 0

    # Initialize tqdm progress bar for the loop
    with tqdm(total=len(instances), desc="Checking health", unit="instance") as pbar:
        while len(health_set.keys()) != len(instances):
            count += 1
            for _, row in instances.iterrows():
                try:
                    re.get("http://" + row.get('public_ipv4') + ":8181/health", timeout=1)
                    health_set[row.get('uuid')] = True
                    pbar.update(1)
                except Exception as _:
                    time.sleep(1)
                    # Log to tqdm (not interrupting the progress bar)
                    pbar.set_postfix({"failed": row.get('uuid'), "retry": count}, refresh=True)

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

def fix_private_key_permissions(private_key_path):
    """
    This function ensures that the private key file has the correct permissions (600).
    This is typically required for SSH private keys to ensure that only the owner can read/write it.
    """
    # Check if the file exists
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"The specified private key file does not exist: {private_key_path}")
    
    # Check the current file permissions
    current_permissions = oct(os.stat(private_key_path).st_mode)[-3:]
    
    # Set the correct permissions (600)
    if current_permissions != '600':
        print(f"Fixing permissions for {private_key_path}. Current permissions: {current_permissions}")
        os.chmod(private_key_path, 0o600)  # Set permission to 600 (read/write for owner only)
        print(f"Permissions fixed to 600 for {private_key_path}")
    else:
        pass

private_key_path = config.cluster.keypair.private

if private_key_path:
    try:
        # Attempt to fix the permissions if the key exists
        fix_private_key_permissions(private_key_path)
    except FileNotFoundError as e:
        print("Private key pair not found, generating one...")
        
        # Extract the directory and file name from the private key path
        key_dir = os.path.dirname(private_key_path)
        key_name = os.path.basename(private_key_path)
        
        # Create the directory if it doesn't exist
        os.makedirs(key_dir, exist_ok=True)
        
        # Generate SSH key pair
        generate_ssh_key_pair(private_key_path)

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
    if (init):
        return idch_build_node(config.master, config.master.init_resources)
    else:
        return idch_build_node(config.master, config.master.resources)

def idch_build_worker_node():
    # perhaps add looping
    master_node_ip = "192.168.0.1"
    
    return idch_build_node(config.worker, config.worker.resource, environments={
        "MASTER_NODE_IP": master_node_ip
    })
    
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


###################### Init Config and Dependency ######################

import sys
from pprint import pprint

def print_help(menu):
    """Print available commands for the current level."""
    print("Available commands:")
    for key in menu:
        print(f"  {key}")
    print()
    
def process_args(menu, args, level=0):
    """Recursively process arguments based on the menu structure."""
    
    if level >= len(args):
        return

    current_arg = args[level]

    if current_arg == "help":
        print_help(menu)
        return

    if current_arg in menu:
        if isinstance(menu[current_arg], dict):
            if ("default" in menu[current_arg]):
                print(menu[current_arg]['default']())
                return
            
            # If the current menu item is a dict, it means there are more options to choose from
            if level == len(args) - 1: print_help(menu[current_arg])
            process_args(menu[current_arg], args, level + 1)
        elif callable(menu[current_arg]):
            # If it's a callable (like a lambda), execute it
            print(menu[current_arg]())
    else:
        print(f"Invalid argument: {current_arg}")

if __name__ == "__main__":
    import sys
    
    menu = {
        "config": lambda: pprint(config),
        "network": {
            "ls": lambda: idch_get("v1/{location}/network/networks")
        },
        "vm": {
            "ls": idch_get_instances,
            "images": {
                "ls": idch_get_os,
                "os": idch_get_os,
                "app": idch_get_app_catalog
            },
            "build": {
                "master": {
                    "init": lambda: idch_build_master_node(init=True),
                    "default": idch_build_master_node
                },
                "worker": idch_build_worker_node
            },  
        },
        "cluster": {
            "start": idch_start_cluster,
            "stop": idch_stop_cluster,
            "sync": idch_sync_cluster,
            "rm": idch_delete_cluster,
            "health": idch_healthcheck_instance
        }
    }
    
    if len(sys.argv) <= 1:
        print_help(menu)
        sys.exit(1)

    arg = sys.argv[1:]
    
    # Call the argument processor
    process_args(menu, arg)