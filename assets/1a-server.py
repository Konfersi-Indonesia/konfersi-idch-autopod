import os
import subprocess
import sys
import json

# Check if Flask is installed; install if not
try:
    from flask import Flask
except ImportError:
    print("Flask not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])

# Import Flask after ensuring it is installed
from flask import Flask, jsonify, request, send_file, abort

# Create the Flask app
app = Flask(__name__)

# Log directory
LOG_DIR = "/var/log"

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Server is healthy"})

@app.route("/logs/<filename>", methods=["GET"])
def get_log_file(filename):
    """Fetch the content of the specified log file.
    
    - If 'n' is provided in the query parameters:
        - n > 0: Return the first 'n' lines (head).
        - n < 0: Return the last 'n' lines (tail).
    - If 'n' is not provided, return the full file content.
    """
    print(filename)
    
    log_file_path = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(log_file_path):
        abort(404, description=f"Log file '{filename}' not found.")
    
    # Get the 'n' query parameter for line count
    n = request.args.get("n", default=None, type=int)
    try:
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()
            if n is None:
                # No 'n' provided, return full content
                return "".join(lines), 200, {"Content-Type": "text/plain"}
            elif n > 0:
                # Return the first 'n' lines
                return "".join(lines[:n]), 200, {"Content-Type": "text/plain"}
            elif n < 0:
                # Return the last 'n' lines
                return "".join(lines[n:]), 200, {"Content-Type": "text/plain"}
            else:
                abort(400, description="'n' must be non-zero.")
    except Exception as e:
        abort(500, description=f"Error reading log file: {str(e)}")


@app.route("/logs", methods=["GET"])
def get_all_logs():
    """Fetch a list of all log files with the '.log' extension."""
    try:
        log_files = [
            file for file in os.listdir(LOG_DIR)
            if file.endswith(".log") and os.path.isfile(os.path.join(LOG_DIR, file))
        ]
        return jsonify(log_files)
    except Exception as e:
        abort(500, description=f"Error listing log files: {str(e)}")

@app.route("/docker/swarm/token", methods=["GET"])
def get_swarm_token():
    """Retrieve the Docker Swarm worker token."""
    try:
        result = subprocess.run(
            ["docker", "swarm", "join-token", "-q", "worker"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return jsonify({"token": result.stdout.strip()}), 200
    except subprocess.CalledProcessError as e:
        abort(500, description=f"Error retrieving swarm token: {e.stderr.strip()}")

# Function to perform a ping test
def ping_test(target):
    try:
        response = subprocess.run(["ping", "-c", "4", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if response.returncode == 0:
            avg_ping = response.stdout.split("avg = ")[1].split("/")[1]  # Extract average ping from ping output
            return {"target": target, "status": "success", "ping_avg_ms": avg_ping}
        else:
            return {"target": target, "status": "failed", "ping_avg_ms": None}
    except Exception as e:
        return {"target": target, "status": "failed", "ping_avg_ms": None, "error": str(e)}

# Function to perform a speed test
def speed_test():
    try:
        result = subprocess.run(["speedtest-cli", "--json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "download_mbps": data["download"] / 1000000,  # Convert download speed to Mbps
                "upload_mbps": data["upload"] / 1000000,      # Convert upload speed to Mbps
                "ping_ms": data["ping"]                        # Get ping in ms
            }
        else:
            return {"error": "Speed test failed"}
    except Exception as e:
        return {"error": str(e)}

# New endpoint for network testing
@app.route("/network/test", methods=["GET"])
def network_test():
    """Perform network tests (ping and speed test) for multiple targets."""
    targets = request.args.get("target", "").split(",")  # Get targets from query parameter
    results = []
    
    # Perform ping test for each target
    for target in targets:
        if target.strip():  # Skip empty targets
            ping_result = ping_test(target)
            results.append(ping_result)
    
    # Perform speed test
    speed_result = speed_test()
    results.append({"speed_test": speed_result})
    
    return jsonify(results)

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
