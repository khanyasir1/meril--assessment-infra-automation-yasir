"""
service_controller.py
- start_service / stop_service / check_service_status
- supports running on a single host or list of hosts
- includes parallel execution helper (ThreadPoolExecutor)
"""
from .utils.ssh import run_command
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_service_status(host: dict, service_name: str) -> dict:
    """
    Check service status on remote host, return simplified status.

    Args:
        host: Dict with host info
        service_name: Name of systemd service

    Returns:
        dict: {
            "host": hostname,
            "service": service_name,
            "status": "active" or "inactive" or "failed" or "unknown",
            "raw": full raw output snippet
        }
    """
    try:
        # Use systemctl is-active for simple status first
        status_output = run_command(host, f"systemctl is-active {service_name}", sudo=False).strip()

        # If is-active fails or returns unknown state, fallback to detailed string parsing
        if status_output not in ['active', 'inactive', 'failed']:
            detail = run_command(host, f"systemctl status {service_name} --no-pager", sudo=False)
            # Parse 'Active: active (running)', 'Active: inactive (dead)', etc.
            import re
            m = re.search(r'Active:\s+(\w+)', detail)
            status = m.group(1) if m else status_output
            raw_output = detail[:300]
        else:
            status = status_output
            raw_output = status_output

        return {
            "host": host['host'],
            "service": service_name,
            "status": status,
            "raw": raw_output
        }
    except Exception as e:
        return {
        "host": host['host'],
        "service": service_name,
        "status": "error",  
        "error": str(e)
    }




def start_service(host: dict, service_name: str) -> dict:
    """Start service via systemctl"""
    try:
        run_command(host, f"systemctl start {service_name}", sudo=True)
        return {
            "host": host['host'],
            "service": service_name,
            "result": "started"
        }
    except Exception as e:
        return {
            "host": host['host'],
            "service": service_name,
            "result": "error",
            "error": str(e)
        }


def stop_service(host: dict, service_name: str) -> dict:
    """Stop service via systemctl"""
    try:
        run_command(host, f"systemctl stop {service_name}", sudo=True)
        return {
            "host": host['host'],
            "service": service_name,
            "result": "stopped"
        }
    except Exception as e:
        return {
            "host": host['host'],
            "service": service_name,
            "result": "error",
            "error": str(e)
        }


def restart_service(host: dict, service_name: str) -> dict:
    """Restart service via systemctl"""
    try:
        run_command(host, f"systemctl restart {service_name}", sudo=True)
        return {
            "host": host['host'],
            "service": service_name,
            "result": "restarted"
        }
    except Exception as e:
        return {
            "host": host['host'],
            "service": service_name,
            "result": "error",
            "error": str(e)
        }


def start_services_parallel(hosts: list, service_name: str, max_workers: int = 8) -> list:
    """Start same service on multiple hosts in parallel (BONUS FEATURE)"""
    results = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(hosts) or 1)) as ex:
        futures = {ex.submit(start_service, h, service_name): h for h in hosts}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def stop_services_parallel(hosts: list, service_name: str, max_workers: int = 8) -> list:
    """Stop same service on multiple hosts in parallel (BONUS FEATURE)"""
    results = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(hosts) or 1)) as ex:
        futures = {ex.submit(stop_service, h, service_name): h for h in hosts}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def check_status_parallel(hosts: list, service_name: str, max_workers: int = 8) -> list:
    """Check service status on multiple hosts in parallel (BONUS FEATURE)"""
    results = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(hosts) or 1)) as ex:
        futures = {ex.submit(check_service_status, h, service_name): h for h in hosts}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results
