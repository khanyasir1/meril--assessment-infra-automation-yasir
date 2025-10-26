"""
Service Manager CLI
Complete command-line interface for service management operations
"""
import click
import yaml
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# ✅ LOAD ENVIRONMENT VARIABLES FIRST
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Debug: Print if email is configured (can remove after testing)
if os.getenv('SMTP_USER'):
    print(f"✅ Email configured: {os.getenv('SMTP_USER')}")

from src.config_manager import generate_config, validate_config, deploy_config
from src.service_controller import (
    check_service_status,
    start_service,
    stop_service,
    restart_service,
    start_services_parallel,
    stop_services_parallel,
    check_status_parallel
)
from src.monitoring import collect_metrics, generate_report, monitor_service_health

console = Console()


def load_hosts(env: str) -> list:
    """Load hosts from YAML config file"""
    config_path = Path(f"configs/{env}/hosts.yml")
    if not config_path.exists():
        console.print(f"[red]❌ Config file not found: {config_path}[/red]")
        raise click.Abort()
    
    with open(config_path) as f:
        data = yaml.safe_load(f)
        return data.get('hosts', [])


def check_sudo_setup():
    """Check if passwordless sudo is configured (helpful for first-time users)"""
    import subprocess
    try:
        # Try to run sudo systemctl without password
        result = subprocess.run(
            ['sudo', '-n', 'systemctl', 'status', 'nginx'],
            capture_output=True,
            timeout=2
        )
        if result.returncode != 0 and b'password' in result.stderr.lower():
            console.print("\n[yellow]⚠️  WARNING: Passwordless sudo not configured![/yellow]")
            console.print("[yellow]Run this command to fix:[/yellow]")
            console.print('[cyan]echo "$(whoami) ALL=(ALL) NOPASSWD: /bin/systemctl" | sudo tee /etc/sudoers.d/$(whoami)-systemctl[/cyan]')
            console.print('[cyan]sudo chmod 440 /etc/sudoers.d/$(whoami)-systemctl[/cyan]\n')
    except Exception:
        pass  # Ignore errors, this is just a helpful check


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🚀 Service Manager - Infrastructure Automation Tool
    
    Manage service configurations, remote operations, and monitoring.
    """
    pass


# ============================================================================
# CONFIG COMMANDS
# ============================================================================

@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command('generate')
@click.option('--template', '-t', required=True, help='Template file name')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True, help='Environment')
@click.option('--service-name', required=True, help='Service name')
@click.option('--version', default='1.0.0', help='Service version')
@click.option('--port', type=int, required=True, help='Service port')
@click.option('--memory', default='256MB', help='Max memory (e.g., 256MB)')
@click.option('--output', '-o', help='Output file path (optional)')
def generate_config_cmd(template, env, service_name, version, port, memory, output):
    """Generate configuration from template"""
    try:
        params = {
            "service_name": service_name,
            "version": version,
            "environment": env,
            "port": port,
            "max_memory": memory
        }
        
        console.print(f"[cyan]🔧 Generating config from template: {template}[/cyan]")
        config_dict = generate_config(template, env, params)
        
        # Validate
        if validate_config(config_dict):
            console.print("[green]✅ Configuration is valid[/green]")
        else:
            console.print("[red]❌ Configuration validation failed[/red]")
            raise click.Abort()
        
        # Output
        config_json = json.dumps(config_dict, indent=2)
        
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                f.write(config_json)
            console.print(f"[green]✅ Config saved to: {output}[/green]")
        else:
            console.print(Panel(config_json, title="Generated Configuration", border_style="green"))
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@config.command('validate')
@click.argument('config_file', type=click.Path(exists=True))
def validate_config_cmd(config_file):
    """Validate a configuration file"""
    try:
        with open(config_file) as f:
            config_dict = json.load(f)
        
        if validate_config(config_dict):
            console.print(f"[green]✅ {config_file} is valid[/green]")
        else:
            console.print(f"[red]❌ {config_file} is invalid[/red]")
            raise click.Abort()
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@config.command('deploy')
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--target-path', required=True, help='Remote path for config')
@click.option('--host-index', type=int, default=0, help='Host index from hosts.yml (default: 0)')
def deploy_config_cmd(config_file, env, target_path, host_index):
    """Deploy configuration to remote host"""
    try:
        # Load config
        with open(config_file) as f:
            config_dict = json.load(f)
        
        # Load hosts
        hosts = load_hosts(env)
        if host_index >= len(hosts):
            console.print(f"[red]❌ Host index {host_index} out of range (max: {len(hosts)-1})[/red]")
            raise click.Abort()
        
        host = hosts[host_index]
        
        console.print(f"[cyan]🚀 Deploying to {host['host']}...[/cyan]")
        success = deploy_config(config_dict, host, target_path)
        
        if success:
            console.print("[green]✅ Deployment successful[/green]")
        else:
            console.print("[red]❌ Deployment failed[/red]")
            raise click.Abort()
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


# ============================================================================
# SERVICE COMMANDS
# ============================================================================

@cli.group()
def service():
    """Service control commands"""
    pass


@service.command('status')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True, help='Service name')
@click.option('--host-index', type=int, default=0, help='Host index')
@click.option('--all', 'all_hosts', is_flag=True, help='Check all hosts')
def service_status(env, service_name, host_index, all_hosts):
    """Check service status"""
    try:
        hosts = load_hosts(env)
        
        if all_hosts:
            console.print(f"[cyan]🔍 Checking {service_name} on all hosts...[/cyan]")
            results = check_status_parallel(hosts, service_name)
            
            for r in results:
                status_color = "green" if r['status'] == 'active' else "red"
                console.print(f"[{status_color}]{r['host']}: {r['status']}[/{status_color}]")
        else:
            host = hosts[host_index]
            console.print(f"[cyan]🔍 Checking {service_name} on {host['host']}...[/cyan]")
            result = check_service_status(host, service_name)
            
            status_color = "green" if result['status'] == 'active' else "red"
            console.print(f"[{status_color}]Status: {result['status']}[/{status_color}]")
            if 'raw' in result:
                console.print(f"\n{result['raw'][:300]}")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@service.command('start')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True)
@click.option('--host-index', type=int, default=0)
@click.option('--all', 'all_hosts', is_flag=True, help='Start on all hosts')
def service_start(env, service_name, host_index, all_hosts):
    """Start service"""
    try:
        check_sudo_setup()
        
        hosts = load_hosts(env)
        
        if all_hosts:
            console.print(f"[cyan]🚀 Starting {service_name} on all hosts...[/cyan]")
            results = start_services_parallel(hosts, service_name)
            
            for r in results:
                if r['result'] == 'started':
                    console.print(f"[green]✅ {r['host']}: Started[/green]")
                else:
                    console.print(f"[red]❌ {r['host']}: {r.get('error', 'Failed')}[/red]")
        else:
            host = hosts[host_index]
            console.print(f"[cyan]🚀 Starting {service_name} on {host['host']}...[/cyan]")
            result = start_service(host, service_name)
            
            if result['result'] == 'started':
                console.print("[green]✅ Service started[/green]")
            else:
                error_msg = result.get('error', 'Unknown')
                console.print(f"[red]❌ Failed: {error_msg}[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@service.command('stop')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True)
@click.option('--host-index', type=int, default=0)
@click.option('--all', 'all_hosts', is_flag=True, help='Stop on all hosts')
def service_stop(env, service_name, host_index, all_hosts):
    """Stop service"""
    try:
        check_sudo_setup()
        
        hosts = load_hosts(env)
        
        if all_hosts:
            console.print(f"[cyan]🛑 Stopping {service_name} on all hosts...[/cyan]")
            results = stop_services_parallel(hosts, service_name)
            
            for r in results:
                if r['result'] == 'stopped':
                    console.print(f"[green]✅ {r['host']}: Stopped[/green]")
                else:
                    console.print(f"[red]❌ {r['host']}: {r.get('error', 'Failed')}[/red]")
        else:
            host = hosts[host_index]
            console.print(f"[cyan]🛑 Stopping {service_name} on {host['host']}...[/cyan]")
            result = stop_service(host, service_name)
            
            if result['result'] == 'stopped':
                console.print("[green]✅ Service stopped[/green]")
            else:
                error_msg = result.get('error', 'Unknown')
                console.print(f"[red]❌ Failed: {error_msg}[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@service.command('restart')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True)
@click.option('--host-index', type=int, default=0)
def service_restart(env, service_name, host_index):
    """Restart service"""
    try:
        check_sudo_setup()
        
        hosts = load_hosts(env)
        host = hosts[host_index]
        
        console.print(f"[cyan]🔄 Restarting {service_name} on {host['host']}...[/cyan]")
        result = restart_service(host, service_name)
        
        if result['result'] == 'restarted':
            console.print("[green]✅ Service restarted[/green]")
        else:
            console.print(f"[red]❌ Failed: {result.get('error', 'Unknown')}[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


# ============================================================================
# MONITOR COMMANDS
# ============================================================================

@cli.group()
def monitor():
    """Monitoring and reporting commands"""
    pass


@monitor.command('metrics')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True)
@click.option('--host-index', type=int, default=0)
def monitor_metrics(env, service_name, host_index):
    """Collect service metrics"""
    try:
        hosts = load_hosts(env)
        host = hosts[host_index]
        
        console.print(f"[cyan]📊 Collecting metrics from {host['host']}...[/cyan]")
        metrics = collect_metrics(host, service_name)
        
        console.print(Panel(
            f"[green]Host:[/green] {metrics['host']}\n"
            f"[green]Service:[/green] {metrics['service']}\n"
            f"[green]Status:[/green] {metrics['status']}\n"
            f"[green]CPU:[/green] {metrics['cpu']}%\n"
            f"[green]Memory:[/green] {metrics['memory']}%\n"
            f"[green]Time:[/green] {metrics['time']}",
            title="📊 Service Metrics",
            border_style="cyan"
        ))
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@monitor.command('dashboard')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True)
def monitor_dashboard(env, service_name):
    """Display monitoring dashboard for all hosts"""
    try:
        hosts = load_hosts(env)
        
        console.print(f"[cyan]📊 Collecting metrics from all hosts...[/cyan]")
        metrics_list = [collect_metrics(h, service_name) for h in hosts]
        
        generate_report(metrics_list)
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@monitor.command('health')
@click.option('--env', '-e', type=click.Choice(['dev', 'prod']), required=True)
@click.option('--service-name', '-s', required=True)
@click.option('--cpu-threshold', type=float, default=80.0)
@click.option('--memory-threshold', type=float, default=80.0)
@click.option('--host-index', type=int, default=0)
def monitor_health(env, service_name, cpu_threshold, memory_threshold, host_index):
    """Monitor service health with alerts"""
    try:
        hosts = load_hosts(env)
        host = hosts[host_index]
        
        thresholds = {
            "cpu": cpu_threshold,
            "memory": memory_threshold
        }
        
        console.print(f"[cyan]🏥 Health check for {service_name} on {host['host']}...[/cyan]")
        metrics = monitor_service_health(host, service_name, thresholds)
        
        if metrics['alerts']:
            console.print("[yellow]⚠️  Alerts detected:[/yellow]")
            for alert in metrics['alerts']:
                console.print(f"  [red]• {alert}[/red]")
        else:
            console.print("[green]✅ All health checks passed[/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    cli()
