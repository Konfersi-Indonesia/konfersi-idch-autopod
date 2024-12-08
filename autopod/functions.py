from yaml import safe_load
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

from autopod.utils import substitute_env_variables

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
