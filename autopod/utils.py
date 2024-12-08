from types import SimpleNamespace
import pandas as pd
import os
import base64
import json
import re as regex

# Search for a row where the 'name' column equals a variable
def get_row_by_name(df, name):
    filtered_rows = df.loc[df['name'] == name]
    if not filtered_rows.empty:
        return filtered_rows.iloc[0]  # Return the first matching row as a Series
    else:
        return f"No entry found for name: {name}"

def convert_to_dict(key_value_list):
    result = {}
    for item in key_value_list:
        key, value = item.split("=", 1)  # Split at the first '=' character
        result[key] = value
    return result

def handle_json_resp(resp):
    if (resp.status_code != 200):
        raise Exception(f"Non 200 error: {resp.text}")

    try:
        return pd.DataFrame(resp.json())
    except:
        print(resp.text)
        return pd.DataFrame()

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

def print_df(df):
    # Check if df is None
    if df is None:
        print("No Data.")
    # Check if df is a DataFrame
    elif isinstance(df, pd.DataFrame):
        # Check if the DataFrame is empty
        if df.empty:
            print("No Data.")
        else:
            # Handle nullable columns by replacing NaN with 'NULL' (or any placeholder)
            df_filled = df.where(pd.notna(df), 'NULL')
            print(df_filled)
    else:
        # If df is not a DataFrame, print it directly
        print(df)
        
