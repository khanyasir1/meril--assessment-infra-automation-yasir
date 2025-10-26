"""
Tests for config_manager module
"""
import pytest
import json
import os
from src.config_manager import generate_config, validate_config


def test_generate_config_basic():
    """Test basic config generation from template"""
    params = {
        "service_name": "testapp",
        "version": "1.0.0",
        "environment": "dev",
        "port": 8080,
        "max_memory": "256MB"
    }
    
    config = generate_config("service_config_template.json", "dev", params)
    
    assert config is not None
    assert config['service']['name'] == 'testapp'
    assert config['service']['version'] == '1.0.0'
    assert config['service']['env'] == 'dev'
    assert config['service']['port'] == 8080
    assert config['service']['max_memory'] == '256MB'


def test_generate_config_with_defaults():
    """Test config generation with default values"""
    params = {
        "service_name": "myapp",
        "version": "2.0",
        "environment": "prod",
        "port": 9000,
        "max_memory": "512MB"
    }
    
    config = generate_config("service_config_template.json", "prod", params)
    
    # Check defaults are applied
    assert config['service']['healthcheck']['endpoint'] == '/health'
    assert config['service']['healthcheck']['interval'] == '30s'


def test_validate_config_valid():
    """Test validation of valid config"""
    valid_config = {
        "service": {
            "name": "testapp",
            "version": "1.0",
            "env": "dev",
            "port": 8080,
            "max_memory": "256MB",
            "healthcheck": {
                "endpoint": "/health",
                "interval": "30s",
                "timeout": "5s"
            }
        }
    }
    
    assert validate_config(valid_config) == True


def test_validate_config_missing_keys():
    """Test validation fails for missing required keys"""
    invalid_config = {
        "service": {
            "name": "testapp",
            "version": "1.0"
            # Missing: env, port, max_memory, healthcheck
        }
    }
    
    assert validate_config(invalid_config) == False


def test_validate_config_wrong_structure():
    """Test validation fails for wrong structure"""
    invalid_config = {
        "wrong_key": {"data": "value"}
    }
    
    assert validate_config(invalid_config) == False


@pytest.mark.parametrize("port,expected", [
    (8080, True),
    (3000, True),
    (80, True),
    (65535, True),
])
def test_config_with_different_ports(port, expected):
    """Test config generation with various port numbers"""
    params = {
        "service_name": "app",
        "version": "1.0",
        "environment": "dev",
        "port": port,
        "max_memory": "128MB"
    }
    
    config = generate_config("service_config_template.json", "dev", params)
    assert (config['service']['port'] == port) == expected


