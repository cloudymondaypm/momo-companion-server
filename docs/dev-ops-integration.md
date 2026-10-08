# Updating a Source-Based Full Deployment

This guide explains the upstream workflow for pulling, rebuilding and restarting all parts of a full Momo Companion deployment from source.

The original project used this approach on a Linux test server. A related [video tutorial](https://www.bilibili.com/video/BV15H37zHE7Q) shows automated updates and MCP endpoint setup.

## Prerequisites

- A Linux host with the complete application already working.
- JDK 21, Maven, Node.js/npm, and your Python/Conda environment installed.
- A backup of the management database and your private configuration files.
- An understanding of which processes currently own ports `8000`, `8001`, and `8002`.

**Caution:** Updating from Git can introduce breaking database or configuration changes. Test updates before applying them to a production instance. Do not run commands that forcibly kill or reset unrelated processes and uncommitted work.

## 1. Choose a project directory

Example working directory:

```text
/home/system/momo
```

## 2. Clone Momo Companion

```bash
mkdir -p /home/system/momo
cd /home/system/momo
git clone https://github.com/cloudymondaypm/momo-companion-server.git
```

Your source will be at `/home/system/momo/momo-companion-server`.

## 3. Copy your private files

Preserve your existing ASR model and server overrides:

```bash
mkdir -p /home/system/momo/momo-companion-server/main/xiaozhi-server/data
mkdir -p /home/system/momo/momo-companion-server/main/xiaozhi-server/models/SenseVoiceSmall

cp /path/to/old/data/.config.yaml /home/system/momo/momo-companion-server/main/xiaozhi-server/data/.config.yaml
cp /path/to/old/models/SenseVoiceSmall/model.pt /home/system/momo/momo-companion-server/main/xiaozhi-server/models/SenseVoiceSmall/model.pt
```

Keep these private files out of Git and your public build artifacts.

## 4. Create update scripts

### Update the web console (`update_8001.sh`)

```bash
#!/usr/bin/env bash
set -e
cd /home/system/momo/momo-companion-server
git pull --ff-only origin main

cd main/manager-web
npm install
npm run build

mkdir -p /home/system/momo/manager-web
cp -a dist/. /home/system/momo/manager-web/
```

Serve the static `manager-web` build through your existing Nginx/web server configuration; the production build does not need a persistent `npm run serve` process on port 8001.

### Update the Java API (`update_8002.sh`)

```bash
#!/usr/bin/env bash
set -e
cd /home/system/momo/momo-companion-server
git pull --ff-only origin main

cd main/manager-api
mvn clean package -Dmaven.test.skip=true
cp target/xiaozhi-esp32-api.jar /home/system/momo/xiaozhi-esp32-api.jar

# Restart the Java service using your configured service manager.
# Example, if you installed a systemd service named momo-manager-api:
sudo systemctl restart momo-manager-api
```

The example systemd service name is illustrative; use the actual name in your deployment. If you currently start Java by hand, first move it under a process supervisor before automating updates.

### Update the Python server (`update_8000.sh`)

```bash
#!/usr/bin/env bash
set -e
cd /home/system/momo/momo-companion-server
git pull --ff-only origin main

cd main/xiaozhi-server
source "$HOME/.bashrc"
conda activate xiaozhi-esp32-server
pip install -r requirements.txt

# Restart the Python service using your configured service manager.
# Example:
sudo systemctl restart momo-ai-server
```

Adjust the environment name to match your existing Conda setup. A Python process started directly with `python app.py` needs to be stopped and restarted manually, or managed under systemd/supervisor.

Make the three files executable:

```bash
chmod +x update_8001.sh update_8002.sh update_8000.sh
```

## 5. Routine update sequence

```bash
cd /home/system/momo
./update_8001.sh  # Build frontend
./update_8002.sh  # Build/restart Java API
./update_8000.sh  # Update/restart Python AI server
```

Review each script's output before starting the next. If your Git working tree has local changes, save them in commits or stashes before running the update; `git pull --ff-only` will not deliberately discard them.

## 6. Logs and reverse proxy

Check service status with your own systemd service names:

```bash
sudo systemctl status momo-manager-api
sudo systemctl status momo-ai-server
journalctl -u momo-manager-api -f
journalctl -u momo-ai-server -f
```

The upstream project demonstrates [Nginx reverse proxy configuration](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791). Configure the proxy to route requests to the web console, management API and WebSocket server appropriately.

## FAQ

**Why is port 8001 not listening?** In production, `npm run build` generates static HTML/CSS/JavaScript. Serve it with Nginx or another web server instead of keeping the development server running.

**Do I need to apply database SQL migrations manually?** The upstream management API uses Liquibase migrations. Back up first and inspect migration failures if application startup reports problems; never assume migration scripts are risk-free.
