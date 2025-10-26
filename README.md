# ⚙️ Infrastructure Automation — `service_manager`

**Project:** Infrastructure Automation Take-Home Assignment  
**Author:** Yasir Khan  
**Last Updated:** 🗓️ October 26, 2025  

---

## 🚀 Project Summary
`service_manager` is a Python-based CLI automation tool designed to streamline configuration management, remote service operations, and basic monitoring across multiple environments (Dev & Prod).  

It demonstrates **real-world DevOps automation** concepts like:

- Template-based configuration management (Jinja2)  
- Secure remote SSH operations (Fabric / Paramiko)  
- Service lifecycle handling (start / stop / restart / status)  
- Health monitoring & alerting  
- Unit & integration testing with `pytest`  

---

## 📚 Table of Contents
1. [Highlights](#highlights)  
2. [What I Built](#what-i-built)  
3. [Project Structure](#project-structure)  
4. [Quickstart (Dev Demo)](#quickstart)  
5. [Detailed CLI Usage](#detailed-cli-usage)  
6. [Testing](#testing)  
7. [Architecture & Design Decisions](#architecture)  
8. [Production Notes](#prod-notes)  
9. [Monitoring & Alerts](#monitoring)  
10. [Bonus Features](#bonus)  
11. [Challenges & Solutions](#challenges)  
12. [Future Improvements](#future)  
13. [Video Walkthrough](#video)  
14. [Resources](#resources)  
15. [Appendix: Detailed CLI Command Reference](#appendix-detailed-cli-command-reference)  
16. [Submission Checklist](#checklist)

---

## 🌟 Highlights
✅ Modular CLI built with **Click**  
✅ **Jinja2** template rendering for dynamic configs  
✅ **Fabric/Paramiko** for robust SSH management  
✅ **Monitoring + Alerting** (threshold-based)  
✅ Unit + Integration **tests** with coverage  
✅ Bonus features: parallel operations, config diff/backup, and email alerts  

---

## 🧠 What I Built
| Component | Description |
|------------|--------------|
| `config_manager.py` | Generates, validates, and deploys configuration files from templates |
| `service_controller.py` | Starts, stops, restarts, and checks status of remote services |
| `monitoring.py` | Performs system health checks, collects metrics, and sends alerts |
| `utils/ssh.py` | Reusable SSH helper with retry and timeout handling |
| `cli.py` | Main entrypoint for all CLI operations |

---

## 🗂️ Project Structure
```
service_manager_project/
├── configs/
│   ├── dev/
│   │   └── hosts.yml             # Dev environment hosts config
│   ├── prod/
│   │   └── hosts.yml             # Prod environment hosts config
│   └── templates/
│       ├── service_config_template.json   # Jinja2 config template
│       └── monitoring_config_template.json # Template for monitoring configs
├── src/
│   ├── config_manager.py         # Config generation, validation, deployment
│   ├── service_controller.py     # SSH based service lifecycle management
│   ├── monitoring.py             # Metrics collection, alerts, reporting
│   └── utils/
│       ├── ssh.py                # SSH helper functions
│       └── validators.py         # Config validation utilities
├── tests/
│   ├── test_config_manager.py    # Unit tests config manager
│   ├── test_service_controller.py # Unit tests service controller
│   └── test_monitoring.py        # Unit tests monitoring module
├── cli.py                       # CLI entrypoint built with Click
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
└── .env                        # Environment config for email credentials

```

---

## 1. Dev Environment Setup

### 1.1 SSH Setup

- Localhost assumed as dev host
- Setup SSH key for localhost if needed (typically already set)

```bash
ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```
- Test SSH connection:
```bash
ssh localhost whoami  # Should print your username
```

### 1.2 Configure `configs/dev/hosts.yml`

```yaml
hosts:
  - host: localhost
    user: yas  # your username here
```

***

## 2. Dev Configuration Management

### 2.1 Generate Config

```bash
python cli.py config generate \
  --template service_config_template.json \
  --env dev \
  --service-name myapp \
  --port 8080 \
  --memory 256MB \
  --output configs/dev/myapp_config.json
```

### 2.2 Validate Config

```bash
python cli.py config validate configs/dev/myapp_config.json
```

### 2.3 Deploy Config Locally

```bash
python cli.py config deploy configs/dev/myapp_config.json --env dev --target-path /tmp/myapp_config_deployed.json --host-index 0
```

***

## 3. Dev Service Management

### 3.1 Check Service Status

```bash
python cli.py service status --env dev --service-name nginx --host-index 0
```

### 3.2 Stop Service

```bash
python cli.py service stop --env dev --service-name nginx --host-index 0
```

### 3.3 Start Service

```bash
python cli.py service start --env dev --service-name nginx --host-index 0
```

### 3.4 Restart Service

```bash
python cli.py service restart --env dev --service-name nginx --host-index 0
```

***

## 4. Dev Monitoring and Alerts

### 4.1 Collect Metrics

```bash
python cli.py monitor metrics --env dev --service-name nginx --host-index 0
```

### 4.2 Monitoring Dashboard (All Hosts)

```bash
python cli.py monitor dashboard --env dev --service-name nginx
```

### 4.3 Health Check with Thresholds (raising alerts if thresholds crossed)

```bash
python cli.py monitor health --env dev --service-name nginx --cpu-threshold 80 --memory-threshold 75 --host-index 0
```

### 4.4 Test Alert by Setting Low Threshold

```bash
python cli.py monitor health --env dev --service-name nginx --cpu-threshold 0.1 --memory-threshold 0.1 --host-index 0
```

Trigger alert by causing artificial CPU load:

```bash
stress-ng --cpu 2 --timeout 60s &
```

***

## 5. Testing for Dev

Run all tests

```bash
pytest
```

Run tests with coverage

```bash
pytest --cov=src tests/
```

Run specific test file or method

```bash
pytest tests/test_config_manager.py -v
pytest tests/test_config_manager.py::test_generate_config_basic -v
```

***

# Prod Environment Setup & Usage Guide

***

## 1. Prod Environment Setup

### 1.1 Provision Instances & Setup

- Create 3 EC2 Ubuntu 22.04 instances
- Provide SSH keys and write public IPs in `configs/prod/hosts.yml`:

```yaml
hosts:
  - host: 13.218.146.104
    user: ubuntu
    key_filename: ~/.ssh/yasir-aws-meril.pem
    name: web-app-03

  - host: 3.95.177.123
    user: ubuntu
    key_filename: ~/.ssh/yasir-aws-meril.pem
    name: web-app-02
  
  - host: 98.93.221.0
    user: ubuntu
    key_filename: ~/.ssh/yasir-aws-meril.pem
    name: web-app-01
```

### 1.2 Setup Passwordless sudo on Prod Hosts

On each host:

```bash
sudo visudo
```

Add to sudoers:

```
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl, /usr/bin/apt, /usr/sbin/service, /bin/mkdir, /bin/cp
```

***

## 2. Prod Configuration Management & Deployment

### 2.1 Generate Configuration

```bash
python cli.py config generate \
  --template service_config_template.json \
  --env prod \
  --service-name myapp \
  --port 8080 \
  --memory 512MB \
  --output configs/prod/myapp_config.json
```

### 2.2 Ensure Remote Directory Exists

```bash
ssh -i ~/.ssh/yasir-aws-meril.pem ubuntu@13.218.146.104 "sudo mkdir -p /etc/myapp && sudo chown ubuntu:ubuntu /etc/myapp"
```

### 2.3 Deploy Configuration to Hosts

Deploy to first host:

```bash
python cli.py config deploy configs/prod/myapp_config.json --env prod --target-path /etc/myapp/config.json --host-index 0
```

Deploy sequentially to all prod hosts:

```bash
for i in 0 1 2; do
  python cli.py config deploy configs/prod/myapp_config.json --env prod --target-path /etc/myapp/config.json --host-index $i
done
```

***

## 3. Prod Service Management

### 3.1 Check Status on All Hosts

```bash
python cli.py service status --env prod --service-name myapp --all
```

### 3.2 Start Service on All Hosts

```bash
python cli.py service start --env prod --service-name myapp --all
```

### 3.3 Stop Service on All Hosts

```bash
python cli.py service stop --env prod --service-name myapp --all
```

### 3.4 Restart Service on First Host

```bash
python cli.py service restart --env prod --service-name myapp --host-index 0
```

***

## 4. Prod Monitoring & Alerts

### 4.1 Dashboard for All Hosts

```bash
python cli.py monitor dashboard --env prod --service-name myapp
```

### 4.2 Health Check & Alerts

```bash
python cli.py monitor health --env prod --service-name myapp --cpu-threshold 80 --memory-threshold 80 --host-index 0
```

### 4.3 Force Alert (Low Threshold)

```bash
python cli.py monitor health --env prod --service-name myapp --cpu-threshold 1 --memory-threshold 1 --host-index 0
```

Generate CPU load on remote host (in other terminal):

```bash
ssh -i ~/.ssh/yasir-aws-meril.pem ubuntu@13.218.146.104 "stress-ng --cpu 2 --timeout 60s &"
```

***

## 5. Prod Testing

Run pytest as usual:

```bash
pytest
pytest --cov=src tests/
```

***


## 🧩 Bonus Features

✨ Parallel operations  
✨ Config diff + backup before deploy  
✨ Email notifications on threshold breach  
✨ Stress-test support (`stress-ng`) for alert testing  

---

## ⚔️ Challenges & Solutions

| Challenge | Solution |
|------------|-----------|
| SSH flakiness | Retries + Fabric timeouts |
| Inconsistent service outputs | Used `systemctl is-active` |
| Alert spam | Added cooldown & threshold logic |

---

## 🔮 Future Improvements

- Persistent metrics (Prometheus/Grafana)  
- Dockerized tool for CI/CD pipelines  
- REST API wrapper  
- Vault integration for secrets  
- Slack/PagerDuty notification hooks  

---

## 🎥 Video Walkthrough

**Script Checklist**
1. 30s — Intro  
2. 60s — CLI demo  
3. 90s — Key features  
4. 90s — Tests  
5. 90s — Code walkthrough  
6. 30s — Bonus & trade-offs  
7. 30s — Wrap-up  

📺 **Thumbnail Idea**  
> Text: “Infra Automation — Demo + Tests”  
> Subtext: “8-min walkthrough | Python • SSH • Jinja2”  
> Size: 1280×720px | Bold font | Contrast colors  

---

## 📚 Resources

- [Fabric Docs](https://www.fabfile.org/)  
- [Paramiko Docs](https://www.paramiko.org/)  
- [Jinja2 Docs](https://jinja.palletsprojects.com/)  
- [Click CLI](https://click.palletsprojects.com/)  
- [pytest](https://docs.pytest.org/)  
- [stress-ng](https://kernel.org/pub/linux/utils/kernel/stress/)  

---

## 🧾 Appendix: Detailed CLI Command Reference (Dev & Prod)

### 🧩 Dev Environment Commands
```bash
python cli.py config generate --template service_config_template.json --env dev --service-name myapp --port 8080 --memory 256MB --output configs/dev/myapp.json
python cli.py config validate configs/dev/myapp.json
python cli.py config deploy configs/dev/myapp.json --env dev --target-path /tmp/myapp_config.json --host-index 0
python cli.py service status --env dev --service-name nginx --host-index 0
python cli.py service start --env dev --service-name nginx --host-index 0
python cli.py service stop --env dev --service-name nginx --host-index 0
python cli.py service restart --env dev --service-name nginx --host-index 0
python cli.py monitor metrics --env dev --service-name nginx --host-index 0
python cli.py monitor dashboard --env dev --service-name nginx
python cli.py monitor health --env dev --service-name nginx --cpu-threshold 80 --memory-threshold 75 --host-index 0
pytest
pytest --cov=src tests/
pytest tests/test_config_manager.py -v
```

---

### 🚀 Prod Environment Commands
```bash
python cli.py config generate --template service_config_template.json.j2 --env prod --service-name myapp --port 8080 --memory 512MB --output configs/prod/myapp.json
ssh -i ~/.ssh/yasir-aws-meril.pem ubuntu@<host-ip> "sudo mkdir -p /etc/myapp && sudo chown ubuntu:ubuntu /etc/myapp"
python cli.py config deploy configs/prod/myapp.json --env prod --target-path /etc/myapp/config.json --host-index 0
for i in 0 1 2; do
  python cli.py config deploy configs/prod/myapp.json --env prod --target-path /etc/myapp/config.json --host-index $i
done
python cli.py service status --env prod --service-name myapp --all
python cli.py service start --env prod --service-name myapp --all
python cli.py service stop --env prod --service-name myapp --all
python cli.py service restart --env prod --service-name myapp --host-index 0
python cli.py monitor dashboard --env prod --service-name myapp
python cli.py monitor health --env prod --service-name myapp --cpu-threshold 80 --memory-threshold 80 --host-index 0
python cli.py monitor health --env prod --service-name myapp --cpu-threshold 1 --memory-threshold 1 --host-index 0
ssh -i ~/.ssh/yasir-aws-meril.pem ubuntu@13.218.146.104 "stress-ng --cpu 2 --timeout 60s &"
pytest
pytest --cov=src tests/
```

---

### ⚙️ Bonus Feature Commands
```bash
python cli.py service start --env prod --service-name myapp --all
python cli.py config deploy configs/prod/myapp.json --env prod --target-path /etc/myapp/config.json --host-index 0
python cli.py monitor health --env prod --service-name myapp --cpu-threshold 80 --memory-threshold 80 --host-index 0
```

💡 *Use this appendix for quick demo/testing across both environments.*

---

## ✅ Submission Checklist

- [x] Code + tests included  
- [x] `requirements.txt` updated  
- [x] README.md complete  
- [x] Tests passing (`pytest`)  
- [x] Video walkthrough uploaded (unlisted)  
- [x] Thumbnail added (`docs/video_thumbnail.png`)  
- [x] Example configs for dev & prod  
````
