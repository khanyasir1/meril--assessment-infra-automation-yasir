"""
SSH utilities for remote operations
Supports both localhost and remote hosts with key-based auth
"""
from fabric import Connection
import os


def get_connection(host_config: dict) -> Connection:
    """
    Create Fabric Connection from host config
    
    Args:
        host_config: Dict with 'host', 'user', and optionally 'key_filename'
    
    Returns:
        Connection: Fabric connection object
    """
    connect_kwargs = {}
    
    # Handle key-based authentication
    if 'key_filename' in host_config and host_config['key_filename']:
        key_path = os.path.expanduser(host_config['key_filename'])
        if os.path.exists(key_path):
            connect_kwargs['key_filename'] = key_path
    
    conn = Connection(
        host=host_config['host'],
        user=host_config.get('user', 'ubuntu'),
        connect_kwargs=connect_kwargs
    )
    
    return conn


def run_command(host_config: dict, command: str, sudo: bool = False) -> str:
    """
    Execute command on remote host via SSH
    
    Args:
        host_config: Dict with host connection details
        command: Command to execute
        sudo: Whether to run with sudo
    
    Returns:
        str: Command output (stdout)
    
    Raises:
        Exception: If command fails
    """
    try:
        conn = get_connection(host_config)
        
        if sudo:
            result = conn.sudo(command, hide=True, warn=True)
        else:
            result = conn.run(command, hide=True, warn=True)
        
        if result.failed:
            raise Exception(f"Command failed: {result.stderr}")
        
        return result.stdout.strip()
    
    except Exception as e:
        raise Exception(f"SSH command failed on {host_config['host']}: {str(e)}")


def upload_file(host_config: dict, local_path: str, remote_path: str) -> bool:
    """
    Upload local file to remote host via SFTP
    
    Args:
        host_config: Dict with host connection details
        local_path: Local file path
        remote_path: Remote destination path
    
    Returns:
        bool: True if upload successful
    
    Raises:
        Exception: If upload fails
    """
    try:
        conn = get_connection(host_config)
        
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            conn.run(f"mkdir -p {remote_dir}", hide=True, warn=True)
        
        conn.put(local_path, remote_path)
        return True
    
    except Exception as e:
        raise Exception(f"File upload failed to {host_config['host']}: {str(e)}")


def download_file(host_config: dict, remote_path: str, local_path: str) -> bool:
    """
    Download file from remote host via SFTP
    
    Args:
        host_config: Dict with host connection details
        remote_path: Remote file path
        local_path: Local destination path
    
    Returns:
        bool: True if download successful
    """
    try:
        conn = get_connection(host_config)
        
        # Create local directory if needed
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        
        conn.get(remote_path, local_path)
        return True
    
    except Exception as e:
        raise Exception(f"File download failed from {host_config['host']}: {str(e)}")
