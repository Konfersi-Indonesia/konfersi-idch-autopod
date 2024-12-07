#!/bin/bash

echo "Print all env for checking"
printenv

# Update package list
echo "Updating package list..."
sudo apt update -y

# Install Python 3 and pip
echo "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip

# Install speedtest-cli using pip
echo "Installing speedtest-cli..."
sudo pip3 install speedtest-cli

echo "Installation complete!"


# Optional: Install additional dependencies (e.g., virtualenv, numpy)
# echo "Installing additional dependencies..."
# apt install -y python3-venv python3-numpy

echo "Python 3 and pip have been installed successfully."

# Check Python and pip versions
python3 --version
pip3 --version

python3 -m pip install flask

echo "Installation complete."

# Loop through all .sh files in the current directory and process them
echo "Making all .sh files in the current directory executable and changing ownership..."
for script in *.sh; do
    if [ -f "$script" ]; then
        echo "Processing $script..."
        # Change ownership to ubuntu:ubuntu (no sudo)
        chown "$USER":"$USER" "$script"
        # Make the file executable
        chmod +x "$script"
    fi
done

echo "All .sh files have been processed."

# Define variables for paths and other values
SCRIPT_PATH="${CLOUD_INIT_WORKDIR:-/home/ubuntu}" 
SYSTEMD_SERVICE_PATH="/etc/systemd/system/server.service"
NODE_ROLE="${NODE_ROLE:-master}"
SERVER_SCRIPT="1a-server.py"
INIT_SCRIPT="1b-init-runner.py"

LOG_FILE="/var/log/$SERVER_SCRIPT.log"

# Create the systemd service for running the Python script on startup
echo "Creating systemd service..."
cat <<EOF > "$SYSTEMD_SERVICE_PATH"
[Unit]
Description=Run the init script at startup
After=network.target

[Service]
ExecStart=/usr/bin/python3 "$SCRIPT_PATH/$SERVER_SCRIPT"
WorkingDirectory=$SCRIPT_PATH
Restart=on-failure
User=root
Group=root
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF

echo "Systemd service created."

# Enable the systemd service without starting it immediately
echo "Enabling the systemd service to start on boot..."
systemctl daemon-reload
systemctl enable server.service
systemctl start server.service

echo "Running python scripts worker"

python3 "${SCRIPT_PATH}/${INIT_SCRIPT}" --workdir ${SCRIPT_PATH} --role ${NODE_ROLE} &

echo "Setup complete."
