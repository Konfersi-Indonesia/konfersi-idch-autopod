import pandas as pd
from autopod_base import config, idch_build_master_node, idch_build_worker_node, idch_delete_cluster, idch_get, idch_get_app_catalog, idch_get_instances, idch_get_os, idch_healthcheck_instance, idch_start_cluster, idch_stop_cluster, idch_sync_cluster
import sys
from pprint import pprint
import subprocess

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

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

def idch_open_shell(argv_no=3):
    name = sys.argv[argv_no]
    
    df = idch_get_instances()
    if (len(df) == 0): return

    ssh_command = df.loc[df['name'] == name, 'command'].values[0]
    
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
                result = menu[current_arg]['default']()
                print_df(result)
                return
            
            # If the current menu item is a dict, it means there are more options to choose from
            if level == len(args) - 1: print_help(menu[current_arg])
            process_args(menu[current_arg], args, level + 1)
        elif callable(menu[current_arg]):
            # If it's a callable (like a lambda), execute it
            result = menu[current_arg]()
            print_df(result)
    else:
        print(f"Invalid argument: {current_arg}")

if __name__ == "__main__":    
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
            "shell": idch_open_shell
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