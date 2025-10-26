"""
Monitoring and reporting module
Collects metrics, generates reports, sends notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rich.console import Console
from rich.table import Table
from datetime import datetime
from .utils.ssh import run_command

console = Console()


def collect_metrics(host: dict, service_name: str) -> dict:
    """Collect service metrics from remote host"""
    metrics = {
        "host": host['host'],
        "service": service_name,
        "status": "unknown",
        "cpu": 0.0,
        "memory": 0.0,
        "uptime": "N/A",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Check service status
        status_output = run_command(host, f"systemctl is-active {service_name}", sudo=False)
        metrics['status'] = status_output.strip() if status_output else "inactive"
        
        # Get CPU and Memory - IMPROVED METHOD
        try:
            # Method 1: Get PID from systemd
            pid_cmd = f"systemctl show {service_name} --property=MainPID --value"
            pid_output = run_command(host, pid_cmd, sudo=False)
            pid = pid_output.strip()
            
            if pid and pid != "0":
                # Use ps with CORRECT format
                ps_cmd = f"ps -p {pid} -o %cpu=,%mem="
                ps_output = run_command(host, ps_cmd, sudo=False)
                
                if ps_output and ps_output.strip():
                    parts = ps_output.strip().split()
                    if len(parts) >= 2:
                        try:
                            metrics['cpu'] = float(parts[0])
                            metrics['memory'] = float(parts[1])
                        except ValueError:
                            pass
            
            # Method 2: Fallback - get ALL PIDs for service name
            if metrics['cpu'] == 0.0:
                # Get all PIDs matching service name
                pgrep_cmd = f"pgrep -f {service_name}"
                pgrep_output = run_command(host, pgrep_cmd, sudo=False)
                
                if pgrep_output.strip():
                    pids = pgrep_output.strip().split('\n')
                    # Sum CPU/Memory for all PIDs
                    total_cpu = 0.0
                    total_mem = 0.0
                    
                    for pid in pids[:5]:  # Check first 5 PIDs
                        if pid.strip():
                            try:
                                ps_cmd = f"ps -p {pid.strip()} -o %cpu=,%mem="
                                ps_out = run_command(host, ps_cmd, sudo=False)
                                if ps_out.strip():
                                    parts = ps_out.strip().split()
                                    if len(parts) >= 2:
                                        total_cpu += float(parts[0])
                                        total_mem += float(parts[1])
                            except:
                                pass
                    
                    metrics['cpu'] = total_cpu
                    metrics['memory'] = total_mem
        
        except Exception as e:
            print(f"Debug: Could not get metrics: {e}")
    
    except Exception as e:
        metrics['status'] = f"error: {str(e)[:50]}"
    
    return metrics


def generate_report(metrics: list) -> str:
    """Generate ASCII table report from metrics"""
    table = Table(title="🖥️  Service Metrics Dashboard", show_header=True, header_style="bold cyan")
    
    table.add_column("Host", style="green")
    table.add_column("Service", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("CPU(%)", justify="right")
    table.add_column("Memory(%)", justify="right")
    table.add_column("Checked At", style="dim")
    
    for m in metrics:
        status_color = "green" if m['status'] == 'active' else "red"
        table.add_row(
            m['host'],
            m['service'],
            f"[{status_color}]{m['status']}[/{status_color}]",
            f"{m['cpu']:.1f}",
            f"{m['memory']:.1f}",
            str(m['time'])
        )
    
    console.print(table)
    
    # Return plain text version for logging
    report_lines = ["\n=== Service Metrics Report ==="]
    for m in metrics:
        report_lines.append(
            f"Host: {m['host']} | Service: {m['service']} | "
            f"Status: {m['status']} | CPU: {m['cpu']:.1f}% | Memory: {m['memory']:.1f}%"
        )
    
    return "\n".join(report_lines)


def send_notification(message: str, severity: str = "INFO", email: bool = False) -> bool:
    """
    Send notification via console or email
    
    Args:
        message: Notification message
        severity: INFO, WARNING, ERROR, CRITICAL
        email: If True, send actual email (requires config)
    
    Returns:
        bool: True if notification sent successfully
    """
    severity_colors = {
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red"
    }
    
    color = severity_colors.get(severity, "white")
    console.print(f"[{color}]🔔 [{severity}] {message}[/{color}]")
    
    # Send email if configured
    if email:
        try:
            return send_email_notification(message, severity)
        except Exception as e:
            console.print(f"[red]Email notification failed: {e}[/red]")
            return False
    
    return True


def send_email_notification(message: str, severity: str) -> bool:
    """
    Send email notification using SMTP with detailed alert information
    
    Configuration in environment variables:
    - SMTP_HOST: SMTP server (default: smtp.gmail.com)
    - SMTP_PORT: SMTP port (default: 587)
    - SMTP_USER: Email username
    - SMTP_PASS: Email password
    - ALERT_EMAIL_TO: Recipient email
    """
    import os
    
    # Email configuration
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER', 'your-email@gmail.com')
    smtp_pass = os.getenv('SMTP_PASS', 'your-app-password')
    recipient = os.getenv('ALERT_EMAIL_TO', 'admin@example.com')
    
    # Check if configured
    if smtp_user == 'your-email@gmail.com':
        console.print("[yellow]⚠️  Email not configured. Set environment variables:[/yellow]")
        console.print("[yellow]SMTP_USER, SMTP_PASS, ALERT_EMAIL_TO[/yellow]")
        return False
    
    # Parse message to extract details
    # Format: "host - service: Alert message"
    try:
        if ' - ' in message and ': ' in message:
            host_service, alert_detail = message.split(': ', 1)
            host, service = host_service.split(' - ', 1)
        else:
            host = "Unknown"
            service = "Unknown"
            alert_detail = message
    except:
        host = "Unknown"
        service = "Unknown"
        alert_detail = message
    
    # Create HTML email body with proper formatting
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f44336; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
            .alert-box {{ background-color: #fff; border-left: 4px solid #f44336; padding: 15px; margin: 15px 0; }}
            .detail {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #000; }}
            .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🚨 Service Manager Alert</h2>
            </div>
            <div class="content">
                <div class="alert-box">
                    <div class="detail">
                        <span class="label">Severity:</span>
                        <span class="value" style="color: #f44336; font-weight: bold;">{severity}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Host:</span>
                        <span class="value">{host}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Service:</span>
                        <span class="value">{service}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Alert:</span>
                        <span class="value" style="font-size: 16px; font-weight: bold;">{alert_detail}</span>
                    </div>
                    <div class="detail">
                        <span class="label">Time:</span>
                        <span class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                    <strong>⚠️ Action Required:</strong><br>
                    Please investigate the service immediately and take necessary action.
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from <strong>Service Manager</strong>.</p>
                    <p>Do not reply to this email. For support, contact your DevOps team.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback
    plain_body = f"""
Service Manager Alert
{'=' * 50}

Severity: {severity}
Host: {host}
Service: {service}
Alert: {alert_detail}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 50}

⚠️ Action Required:
Please investigate the service immediately and take necessary action.

---
This is an automated alert from Service Manager.
Do not reply to this email.
    """
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = smtp_user
    msg['To'] = recipient
    msg['Subject'] = f"🚨 [{severity}] {service} Alert on {host}"
    
    # Attach both plain text and HTML versions
    msg.attach(MIMEText(plain_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    # Send email
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        console.print(f"[green]✅ Email sent to {recipient}[/green]")
        return True
    
    except Exception as e:
        console.print(f"[red]❌ Email failed: {e}[/red]")
        return False


def monitor_service_health(host: dict, service_name: str, thresholds: dict = None) -> dict:
    """Monitor service and send alerts if thresholds exceeded (BONUS FEATURE)"""
    if thresholds is None:
        thresholds = {"cpu": 80.0, "memory": 80.0}
    
    metrics = collect_metrics(host, service_name)
    
    # Check thresholds
    alerts = []
    
    if metrics['cpu'] > thresholds['cpu']:
        alerts.append(f"CPU usage high: {metrics['cpu']:.1f}%")
    
    if metrics['memory'] > thresholds['memory']:
        alerts.append(f"Memory usage high: {metrics['memory']:.1f}%")
    
    if metrics['status'] not in ['active', 'running']:
        alerts.append(f"Service not active: {metrics['status']}")
    
    # Send notifications
    import os
    # Check if email is configured
    email_enabled = os.getenv('SMTP_USER') and os.getenv('SMTP_USER') != 'your-email@gmail.com'
    
    for alert in alerts:
        send_notification(
            f"{host['host']} - {service_name}: {alert}",
            severity="WARNING",
            email=email_enabled  # Auto-enable if configured
        )
    
    metrics['alerts'] = alerts
    return metrics
