import subprocess
import threading
import argparse
import json
import yaml

# Set up argument parsing
parser = argparse.ArgumentParser(description="Script Runner for Docker and Swarm setup.")
parser.add_argument("--workdir", type=str, default="/home/ubuntu", help="Directory for work (default: /home/ubuntu)")
parser.add_argument("--logdir", type=str, default="/var/log", help="Directory for logs (default: /var/log)")
parser.add_argument("--role", type=str, choices=["master", "worker", "test"], help="Role for the node (default: test)")
parser.add_argument("--log-file", type=str, default="/var/log/init-runner-executor.log", help="Set location to write log (default: /var/log/init-runner-executor.log")
parser.add_argument("--configfile", type=str, default="config.yaml", help="Path to the YAML config file (default: config.yaml)")

# Parse arguments
args = parser.parse_args()

workdir = args.workdir
logdir = args.logdir
role = args.role
log_file = args.log_file
configfile = args.configfile

# Function to log JSON formatted messages
def log_json(status, message, **kwargs):
    log_message = {
        "status": status,
        "message": message,
        "role": role,
    }
    log_message.update(kwargs)

    # Open the log file and append the log message
    with open(log_file, 'a') as log:
        log.write(json.dumps(log_message) + "\n")  # Write log message and add newline


# Log initial setup
log_json("init", f"Role assigned to: {role}", workdir=workdir, logdir=logdir)

def load_config(configfile):
    with open(configfile, 'r') as file:
        config = yaml.safe_load(file)
    return config
        

# Load the configuration from the provided YAML file
config = load_config(configfile)

# Initialize the script list
scripts = []

if "global" in config:
    scripts += config["global"]
    
if role:
    scripts += config[role]
    
print("Script to run:")
for script in scripts:
    print(script)

# Function to get the last 10 lines of a log file
def get_log_tail(log_file, lines=10):
    try:
        with open(log_file, 'r') as file:
            return ''.join(file.readlines()[-lines:])
    except FileNotFoundError:
        return "Log file not found."

# Function to run a script and log the output
def run_script(script, counters, lock):
    log_file = f"{logdir}/{script.split('/')[-1]}.log"
    command = f"bash {workdir}/{script}"
    
    log_json("running", f"Running script: {script}", script=script, script_status="running", log_file=log_file)
    
    with open(log_file, 'w') as log:
        result = subprocess.run(command, shell=True, stdout=log, stderr=subprocess.STDOUT)
        log_tail = get_log_tail(log_file)
        
        # Using lock to safely update shared counters
        with lock:
            if result.returncode != 0:
                log_json("running", f"Script {script} failed. See log for details.", script=script, log=log_tail, script_status="failed", log_file=log_file)
                counters['failed'].append(log_file)
            else:
                log_json("running", f"Script {script} executed successfully.", script=script, log=log_tail, script_status="done", log_file=log_file)
                counters['success'].append(log_file)

# Function to run a list of scripts asynchronously
def run_scripts_async(scripts_list, counters, lock):
    threads = []
    for script in scripts_list:
        thread = threading.Thread(target=run_script, args=(script, counters, lock))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

# Initialize counters and log file list
counters = {'success': [], 'failed': []}  # Use a dictionary to store the success and failure counts
lock = threading.Lock()  # Lock to ensure thread-safe updates to counters

# Run scripts sequentially and asynchronously based on structure
for script in scripts:
    if isinstance(script, list):
        # If item is a list, run the scripts asynchronously
        run_scripts_async(script,counters, lock)
    else:
        # If item is not a list, run it sequentially
        run_script(script, counters, lock)
        
result = []

for item in counters["success"]:
    result.append({
        "status": "success",
        "logfile": item,
        "log": get_log_tail(item)
    })
    
for item in counters["failed"]:
    result.append({
        "status": "failed",
        "logfile": item,
        "log": get_log_tail(item)
    })

# Final log message after all scripts run
log_json("done", "All scripts execution completed", script_success=len(counters['success']), script_failed=len(counters['failed']), result=result)
