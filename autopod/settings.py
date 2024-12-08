import os
import pandas as pd

from autopod.functions import fix_private_key_permissions, generate_ssh_key_pair, load_config
from autopod.utils import map_to_namespace


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


config = map_to_namespace(load_config("config.yaml"))

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