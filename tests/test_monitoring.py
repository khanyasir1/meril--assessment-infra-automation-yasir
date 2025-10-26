"""
Tests for monitoring module
"""
import pytest
from unittest.mock import patch, MagicMock
from src.monitoring import collect_metrics, generate_report, send_notification


@patch('src.monitoring.run_command')
def test_collect_metrics_active_service(mock_run_command):
    """Test collecting metrics for active service"""
    # Mock SSH responses
    mock_run_command.side_effect = [
        "active",  # systemctl is-active
        "1234",    # MainPID
        "5.2  2.3"  # CPU and memory
    ]
    
    host = {"host": "localhost", "user": "ubuntu"}
    metrics = collect_metrics(host, "nginx")
    
    assert metrics['host'] == 'localhost'
    assert metrics['service'] == 'nginx'
    assert metrics['status'] == 'active'
    assert isinstance(metrics['cpu'], float)
    assert isinstance(metrics['memory'], float)


@patch('src.monitoring.run_command')
def test_collect_metrics_inactive_service(mock_run_command):
    """Test collecting metrics for inactive service"""
    mock_run_command.side_effect = [
        "inactive",  # Service is not running
        "0",         # No PID
    ]
    
    host = {"host": "testhost", "user": "ubuntu"}
    metrics = collect_metrics(host, "myapp")
    
    assert metrics['status'] == 'inactive'


def test_generate_report():
    """Test report generation"""
    metrics_list = [
        {
            "host": "host1",
            "service": "nginx",
            "status": "active",
            "cpu": 5.2,
            "memory": 10.5,
            "time": "2025-10-25 10:00:00"
        },
        {
            "host": "host2",
            "service": "myapp",
            "status": "inactive",
            "cpu": 0.0,
            "memory": 0.0,
            "time": "2025-10-25 10:00:01"
        }
    ]
    
    report = generate_report(metrics_list)
    
    assert isinstance(report, str)
    assert "host1" in report
    assert "host2" in report


def test_send_notification():
    """Test notification sending"""
    result = send_notification("Test alert", "WARNING")
    assert result == True


@pytest.mark.parametrize("severity", ["INFO", "WARNING", "ERROR", "CRITICAL"])
def test_send_notification_severities(severity):
    """Test notifications with different severity levels"""
    result = send_notification(f"Test {severity} message", severity)
    assert result == True
