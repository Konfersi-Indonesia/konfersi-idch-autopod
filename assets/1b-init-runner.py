import subprocess
import threading
import argparse
import json
import os

# Set up argument parsing
parser = argparse.ArgumentParser(description="Script Runner for Docker and Swarm setup.")
parser.add_argument("--workdir", type=str, default="/home/ubuntu", help="Directory for work (default: /home/ubuntu)")
parser.add_argument("--logdir", type=str, default="/var/log", help="Directory for logs (default: /var/log)")
parser.add_argument("--role", type=str, choices=["master", "worker", "test"], default="test", help="Role for the node (default: test)")
parser.add_argument("--log-file", type=str, default="/var/log/init-runner-executor.log", help="Set location to write log (default: /var/log/init-runner-executor.log")
# Parse arguments
args = parser.parse_args()

workdir = args.workdir
logdir = args.logdir
role = args.role
log_file = args.log_file

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

# List of scripts based on role
scripts = [
    "2-docker-install.sh"
]

# Append scripts based on the role
if role == 'master':
    scripts += [
        "3a-docker-swarm-init.sh",
        [
            "4-docker-portainer-install.sh",
            "5-docker-grafana-install.sh",
            "6-docker-nfs-install.sh",
        ],
        [
            "7-gdrive-copy-content.sh",
            "8-mpich-init.sh"
        ],
    ]
elif role == 'worker':
    scripts += [
        "3b-docker-swarm-join.sh"
    ]
elif role == 'test':
    scripts = [
        "test1.sh",
        ["test2.sh", "test3.sh", "test3a.sh"],
        "test4.sh"
    ]

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