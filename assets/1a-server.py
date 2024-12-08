import os
import subprocess
import argparse
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
            ["sudo", "docker", "swarm", "join-token", "-q", "worker"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return jsonify({"token": result.stdout.strip()}), 200
    except subprocess.CalledProcessError as e:
        abort(500, description=f"Error retrieving swarm token: {e.stderr.strip()}")

# Set up argument parsing
parser = argparse.ArgumentParser(description="Script Runner for Container Healthcheck.")
parser.add_argument("--port", type=int, default="8181", help="Set specific exposed port (default: 8181)")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Set specific exposed host IP (default: 0.0.0.0)")

# Parse arguments
args = parser.parse_args()

# Run the Flask app
if __name__ == "__main__":
    app.run(host=args.host, port=args.port)
