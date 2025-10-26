"""
Tests for service_controller module
"""
import pytest
from unittest.mock import patch, MagicMock
from src.service_controller import (
    check_service_status,
    start_service,
    stop_service,
    restart_service,
    start_services_parallel
)


@patch('src.service_controller.run_command')
def test_check_service_status_active(mock_run_command):
    """Test checking status of active service"""
    mock_run_command.return_value = """
    ● nginx.service - A high performance web server
       Loaded: loaded (/lib/systemd/system/nginx.service)
       Active: active (running) since Mon 2025-10-25 10:00:00 UTC
    """
    
    host = {"host": "localhost", "user": "ubuntu"}
    result = check_service_status(host, "nginx")
    
    assert result['host'] == 'localhost'
    assert result['service'] == 'nginx'
    assert result['status'] == 'active'


@patch('src.service_controller.run_command')
def test_check_service_status_inactive(mock_run_command):
    """Test checking status of inactive service"""
    mock_run_command.return_value = """
    ● myapp.service - My Application
       Loaded: loaded
       Active: inactive (dead)
    """
    
    host = {"host": "testhost", "user": "ubuntu"}
    result = check_service_status(host, "myapp")
    
    assert result['status'] == 'inactive'


@patch('src.service_controller.run_command')
def test_check_service_status_error(mock_run_command):
    """Test error handling when service check fails"""
    mock_run_command.side_effect = Exception("SSH connection failed")
    
    host = {"host": "badhost", "user": "ubuntu"}
    result = check_service_status(host, "nginx")
    
    assert result['status'] == 'error'
    assert 'error' in result


@patch('src.service_controller.run_command')
def test_start_service_success(mock_run_command):
    """Test starting service successfully"""
    mock_run_command.return_value = ""
    
    host = {"host": "localhost", "user": "ubuntu"}
    result = start_service(host, "nginx")
    
    assert result['result'] == 'started'
    assert result['host'] == 'localhost'
    assert result['service'] == 'nginx'


@patch('src.service_controller.run_command')
def test_start_service_failure(mock_run_command):
    """Test start service failure"""
    mock_run_command.side_effect = Exception("Permission denied")
    
    host = {"host": "localhost", "user": "ubuntu"}
    result = start_service(host, "nginx")
    
    assert result['result'] == 'error'
    assert 'error' in result


@patch('src.service_controller.run_command')
def test_stop_service(mock_run_command):
    """Test stopping service"""
    mock_run_command.return_value = ""
    
    host = {"host": "localhost", "user": "ubuntu"}
    result = stop_service(host, "nginx")
    
    assert result['result'] == 'stopped'


@patch('src.service_controller.run_command')
def test_restart_service(mock_run_command):
    """Test restarting service"""
    mock_run_command.return_value = ""
    
    host = {"host": "localhost", "user": "ubuntu"}
    result = restart_service(host, "nginx")
    
    assert result['result'] == 'restarted'


@patch('src.service_controller.start_service')
def test_parallel_execution(mock_start_service):
    """Test parallel service start on multiple hosts"""
    mock_start_service.return_value = {"result": "started"}
    
    hosts = [
        {"host": "host1", "user": "ubuntu"},
        {"host": "host2", "user": "ubuntu"},
        {"host": "host3", "user": "ubuntu"}
    ]
    
    results = start_services_parallel(hosts, "nginx", max_workers=3)
    
    assert len(results) == 3
    assert all(r['result'] == 'started' for r in results)
