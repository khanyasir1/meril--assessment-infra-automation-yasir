import os
import json
import shutil
from jinja2 import Environment, FileSystemLoader
from .utils.validators import validate_config_schema
from .utils.ssh import upload_file, run_command
import difflib


CONFIG_TEMPLATE_DIR = "configs/templates"


def generate_config(template_name: str, env: str, params: dict) -> dict:
    """
    Generate service config from Jinja2 template
    
    Args:
        template_name: Name of template file (e.g., 'service_config_template.json')
        env: Environment name ('dev' or 'prod')
        params: Dictionary of parameters to render template
    
    Returns:
        dict: Rendered configuration as dictionary
    
    Example:
        >>> params = {"service_name": "myapp", "version": "1.0", "environment": "dev", "port": 8080, "max_memory": "256MB"}
        >>> config = generate_config("service_config_template.json", "dev", params)
    """
    env_loader = Environment(loader=FileSystemLoader(CONFIG_TEMPLATE_DIR))
    template = env_loader.get_template(template_name)
    rendered = template.render(**params)
    config = json.loads(rendered)
    return config


def validate_config(config: dict) -> bool:
    """
    Validate configuration against schema
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    return validate_config_schema(config)


def deploy_config(config: dict, target_host: dict, target_path: str) -> bool:
    """
    Deploy configuration to remote host with backup and diff
    
    Args:
        config: Configuration dictionary to deploy
        target_host: Host dict with 'host', 'user', 'key_filename' keys
        target_path: Remote path where config should be deployed
    
    Returns:
        bool: True if deployment successful
    
    Features:
        - Backs up existing config before deployment
        - Shows diff between old and new config
        - Uploads new config via SSH
    """
    # Write config to temp local file first
    temp_path = "/tmp/temp_config.json"
    with open(temp_path, "w") as f:
        json.dump(config, f, indent=4)
    
    # Try to backup old config (if exists on remote)
    backup_path = f"{target_path}.bak"
    try:
        # Create backup by copying remote file
        run_command(target_host, f"cp {target_path} {backup_path}")
        print(f"✅ Backed up old config to {backup_path}")
    except Exception as e:
        print(f"⚠️  No previous config to backup (or backup failed): {e}")
    
    # Try to show diff (bonus feature)
    try:
        # Fetch old config content
        old_content = run_command(target_host, f"cat {target_path}")
        new_content = json.dumps(config, indent=4)
        
        diff = list(difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            fromfile='old_config',
            tofile='new_config',
            lineterm=''
        ))
        
        if diff:
            print("\n📊 Configuration Diff:")
            print("\n".join(diff[:20]))  # Show first 20 lines
            print(f"... (showing first 20 lines)\n")
    except Exception as e:
        print(f"⚠️  Could not generate diff: {e}")
    
    # Upload new config
    try:
        upload_file(target_host, temp_path, target_path)
        print(f"✅ Config deployed successfully to {target_host['host']}:{target_path}")
        return True
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
