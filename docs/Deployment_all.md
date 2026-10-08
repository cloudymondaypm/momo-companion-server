# Full Momo Companion Deployment: AI Server + Management Console

![Full deployment architecture](images/deploy2.png)

This guide covers the full deployment: Python AI server, Java management API, web management console, and their backing services. For an AI server without management, see [Standalone Deployment](Deployment.md).

## Option 1. Docker deployment

> Prebuilt upstream images from version 0.8.2 onward are described as x86-only. ARM64 hosts may require [building the images locally](docker-build.md).

### 1. Install Docker

Install Docker Engine and Docker Compose on your host. See the [upstream Docker installation guide](https://www.runoob.com/docker/ubuntu-docker-install.html) if needed.

You may use the original project's [automatic setup script](#automatic-setup-script) or the [manual setup](#manual-setup).

### Automatic setup script

The upstream one-command installer is maintained by [VanillaNahida](https://github.com/VanillaNahida). See its [video walkthrough](https://www.bilibili.com/video/BV17bbvzHExd/). It was designed mainly for Ubuntu; compatibility with other operating systems is not guaranteed.

**Security:** Review any remote shell script before running it, particularly as root. The command below comes from the upstream project, not from this Momo Companion fork:

```bash
sudo bash -c "$(wget -qO- https://ghfast.top/https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/docker-setup.sh)"
```

The script installs Docker, configures image mirrors, downloads images and speech-recognition models, and guides server setup. Once it finishes, follow [Start the containers](#start-the-containers) and [Configure the three essential settings](#configure-the-three-essential-settings).

### Manual setup

#### 1. Create working directories

Create a project working directory with these subdirectories:

```text
xiaozhi-server/
├── data/
└── models/
    └── SenseVoiceSmall/
```

#### 2. Download the ASR model

The default ASR uses `SenseVoiceSmall`. Download `model.pt` from [ModelScope](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt) or [Baidu Netdisk](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) (access code: `qvna`). Place it in `models/SenseVoiceSmall/model.pt`.

#### 3. Download the configuration files

Download [docker-compose_all.yml](../main/xiaozhi-server/docker-compose_all.yml) into the working directory. Download [config_from_api.yaml](../main/xiaozhi-server/config_from_api.yaml), save it in the `data` directory, and rename it to `.config.yaml`.

On GitHub, open each file and select **Raw** or **Download** to obtain its contents.

The resulting structure should be:

```text
xiaozhi-server/
├── docker-compose_all.yml
├── data/
│   └── .config.yaml
└── models/
    └── SenseVoiceSmall/
        └── model.pt
```

### 2. Back up an existing installation

If you already run the management console, back up its database, any persistent Docker volumes, and your API keys/configuration. An upgrade or `docker compose down` with destructive options can otherwise result in data loss. Do not run `docker compose down -v` against live data without a verified backup.

### 3. Remove old containers if necessary

From the directory containing `docker-compose_all.yml`, the upstream migration procedure uses:

```bash
docker compose -f docker-compose_all.yml down

# Remove only containers that actually exist
docker stop xiaozhi-esp32-server xiaozhi-esp32-server-web xiaozhi-esp32-server-db xiaozhi-esp32-server-redis
docker rm xiaozhi-esp32-server xiaozhi-esp32-server-web xiaozhi-esp32-server-db xiaozhi-esp32-server-redis

# Remove previously cached image tags only if necessary
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest
```

Commands for nonexistent containers/images may report errors. Preserve persistent data volumes unless intentionally replacing them.

### 4. Start the containers

```bash
docker compose -f docker-compose_all.yml up -d
docker logs -f xiaozhi-esp32-server-web
```

Successful management API startup may show a message such as:

```text
INFO  xiaozhi.AdminApplication - Started AdminApplication
http://localhost:8002/xiaozhi/doc.html
```

At this stage the management console may be running while the Python server on port 8000 still needs configuration.

Visit `http://127.0.0.1:8002` from the host machine to open the management console and register the first account. **The first registered account becomes a superadministrator**, with model, user, and parameter management permissions. Subsequent accounts have more limited permissions.

### 5. Configure the three essential settings

#### A. Connect the Python server to the management API

Sign in as superadmin, open **Parameter Management**, and locate `server.secret`. This secret is generated when the management backend is initialized. Copy its **parameter value**; it is required for the Python server to authenticate to `manager-api`.

Edit `data/.config.yaml`:

```yaml
manager-api:
  url: http://xiaozhi-esp32-server-web:8002/xiaozhi
  secret: YOUR_ACTUAL_SERVER_SECRET
```

**Important:** For Docker, use the Compose service hostname `xiaozhi-esp32-server-web` rather than `127.0.0.1`; localhost from inside the Python container would refer to the Python container itself. Keep `server.secret` private.

#### B. Configure at least one LLM provider

In the management console, open **Model Configuration → Large Language Model**. Choose an installed model (the upstream documentation uses Zhipu AI), click **Edit**, and provide a valid API key under **API Key**. Save the configuration.

You can use another compatible LLM provider, including your own supported model endpoint, by configuring the matching provider adapter.

#### C. Set the device-facing endpoints

Once the Python server starts, configure these parameters under **Parameter Management**:

| Parameter | Example on a LAN |
| --- | --- |
| `server.websocket` | `ws://192.168.1.25:8000/xiaozhi/v1/` |
| `server.ota` | `http://192.168.1.25:8002/xiaozhi/ota/` |

Replace `192.168.1.25` with the host address the ESP32 devices can actually reach. For remote devices, use a properly configured public domain and secure endpoints where supported.

### 6. Restart the Python AI server

```bash
docker restart xiaozhi-esp32-server
docker logs -f xiaozhi-esp32-server
```

Confirm that the WebSocket service reports a listening URL. The WebSocket endpoint is not an ordinary browser page; test with a WebSocket client or the digital-human test module.

Now either [compile your own ESP32 firmware](firmware-build.md) or [configure existing supported firmware](firmware-setting.md) to use the OTA URL.

## Option 2. Run all modules from source

### 1. Set up MySQL

If MySQL is installed, create the application database:

```sql
CREATE DATABASE xiaozhi_esp32_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

For a **temporary development environment**, you may start MySQL using Docker:

```bash
docker run --name xiaozhi-esp32-server-db -e MYSQL_ROOT_PASSWORD=CHANGE_ME -p 3306:3306 -e MYSQL_DATABASE=xiaozhi_esp32_server -e TZ=Asia/Shanghai -d mysql:latest
```

Choose a strong database password and configure a persistent volume for production; the command above is a quick demonstration and does not create one.

### 2. Set up Redis

Install Redis or run a development container:

```bash
docker run --name xiaozhi-esp32-server-redis -d -p 6379:6379 redis
```

Do not expose an unauthenticated Redis instance to the internet.

### 3. Start the Java management API

1. Install JDK 21 and set the Java environment variables.
2. Install Maven and set the Maven environment variables.
3. Open `main/manager-api` in VS Code or another Java IDE.
4. Configure the datasource in `src/main/resources/application-dev.yml`:

```yaml
spring:
  datasource:
    username: root
    password: YOUR_DATABASE_PASSWORD
```

Configure Redis in the same file:

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      password:
      database: 0
```

Merge the two `spring` sections when editing the actual YAML file; do not define duplicate top-level keys.

5. Run `src/main/java/xiaozhi/AdminApplication.java` as the Spring Boot application.

Successful startup should report `Started AdminApplication`; API docs are normally accessible at `http://localhost:8002/xiaozhi/doc.html`.

### 4. Start the web management console

1. Install Node.js.
2. Open `main/manager-web` in your editor.
3. Install dependencies and start the development server:

```bash
cd main/manager-web
npm install
npm run serve
```

If `manager-api` does not run at `http://localhost:8002`, edit the API endpoint in `main/manager-web/.env.development`.

Open `http://127.0.0.1:8001` in a browser, register the first account, and configure your LLM provider in **Model Configuration** as described above.

### 5. Prepare Python

Install Conda and create the server environment, including required audio libraries:

```bash
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server
conda install libopus ffmpeg -y

# Linux only, when libiconv.so.2 is missing
conda install libiconv -y
```

On Windows, use **Anaconda Prompt** if convenient:

![Anaconda Prompt](images/conda_env_1.png)

![Conda environment](images/conda_env_2.png)

### 6. Install the Python server dependencies

Clone [this Momo Companion repository](https://github.com/cloudymondaypm/momo-companion-server), then:

```bash
conda activate xiaozhi-esp32-server
cd main/xiaozhi-server
pip install -r requirements.txt
```

### 7. Download the speech model

Place the `SenseVoiceSmall` `model.pt` file from [ModelScope](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt) in `main/xiaozhi-server/models/SenseVoiceSmall/`.

### 8. Configure the management connection

In the console, locate `server.secret` under **Parameter Management** and copy its value. Create `main/xiaozhi-server/data/.config.yaml` based on `config_from_api.yaml`:

```yaml
manager-api:
  url: http://127.0.0.1:8002/xiaozhi
  secret: YOUR_ACTUAL_SERVER_SECRET
```

For a locally run Python process, `127.0.0.1` can work if the API is on the same computer. If it runs elsewhere, use its reachable address.

### 9. Run the Python AI server

```bash
# From main/xiaozhi-server
conda activate xiaozhi-esp32-server
python app.py
```

Verify that the server starts and the logs show a valid WebSocket URL. Make sure `server.websocket` and `server.ota` are also set in the console to device-reachable addresses.

## Configure your devices

After verifying the server and management console, choose one of these approaches:

- [Compile your own ESP32 firmware](firmware-build.md)
- [Configure supported prebuilt ESP32 firmware](firmware-setting.md)

## Related documentation

- [FAQ](FAQ.md)
- [Standalone Deployment](Deployment.md)
- [MQTT+UDP Gateway](mqtt-gateway-integration.md)
- [Home Assistant](homeassistant-integration.md)
- [MCP Endpoint](mcp-endpoint-enable.md)
- [Vision Recognition](mcp-vision-integration.md)
- [News Sources](newsnow_plugin_config.md)
- [Weather Plugin](weather-integration.md)
- [Voice Cloning](huoshan-streamTTS-voice-cloning.md)
- [Performance Testing](performance_tester.md)
