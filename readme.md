# ID Cloudhost Autopod for Konfersi

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Konfersi-Indonesia/konfersi-idch-autopod/main?filepath=autopod.ipynb)


This project is designed to manage node creation and management for IDCloudHost VPS virtual machines to work as a cluster. The notebook automates tasks like node creation, health checking, management (start, stop, delete), cloud-init script generation, MPI cluster readiness, monitoring with Grafana, Portainer setup, and is based on Docker Swarm.

## Features

- Automated creation of VPS nodes
- Health checker for node status
- Start, stop, and delete node management
- Cloud-init script generation for initial setup
- MPI cluster setup
- Monitoring with Grafana
- Portainer setup for container management
- Docker Swarm based cluster management

# WIP

- Adding Support for Kamatera Provider

## Requirements

Before running this project, ensure you have the necessary dependencies installed. These can be installed using the `requirements.txt` file.

### Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Konfersi-Indonesia/konfersi-idch-autopod.git
   cd konfersi-idch-autopod
   ```

2. **Install the required Python dependencies:**

   It's recommended to create a virtual environment to manage dependencies.

   **Using virtualenv**:
   
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

   Then install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   Create a `.env` file with the following variables:

   - `IDCH_TOKEN`: This token can be generated from the [IDCloudHost Console](https://console.idcloudhost.com/user) by creating a new API access.
   - `NODE_PASSWORD`: The password for the nodes that will be created.

   Example `.env` file:

   ```
   IDCH_TOKEN=your_api_token_here
   NODE_PASSWORD=your_node_password_here
   ```

4. **Set up the configuration file:**

   Create and configure the `config.yaml` file for the project. This file should contain the necessary configuration details for node creation, management, and other settings required by the project.

5. **Run the notebook:**

   Once the setup is complete, you can run the notebook `autopod.ipynb`.

   - If you're running it locally, you may need to set up Jupyter Notebook or run it directly from Visual Studio Code.
   - To run Jupyter Notebook:

     ```bash
     jupyter notebook
     ```

     Once Jupyter is running, open `autopod.ipynb` and execute the cells as needed.

## Copyright

© Konfersi Indonesia, 2024.

## Maintainer

- **Alfian Isnan** (alfianisnan26)