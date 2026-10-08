# Standalone Momo Companion Server Deployment

![Standalone deployment architecture](images/deploy1.png)

This guide runs the **standalone AI server without the management console**. For the complete system, see [Full Deployment](Deployment_all.md).

## Option 1. Docker deployment

> The upstream prebuilt images from version 0.8.2 onward are described as x86-only. If you use an ARM64 host, see [Build Docker Images From Source](docker-build.md) and build an image for your architecture.

### 1. Install Docker

Install Docker Engine and Docker Compose for your operating system. For Ubuntu, the [upstream installation guide](https://www.runoob.com/docker/ubuntu-docker-install.html) provides one approach.

### 2. Create the working directories

Choose a working directory, for example `xiaozhi-server`, and create:

```text
xiaozhi-server/
├── data/
└── models/
    └── SenseVoiceSmall/
```

### 3. Download the speech-recognition model

The default standalone ASR uses the offline `SenseVoiceSmall` model. Download `model.pt` using one of the links in [Model Files](#model-files) and place it at `models/SenseVoiceSmall/model.pt`.

### 4. Download Docker Compose and configuration files

Download [docker-compose.yml](../main/xiaozhi-server/docker-compose.yml) from this repository and save it in the `xiaozhi-server` working directory.

Download [config.yaml](../main/xiaozhi-server/config.yaml) and save it as `data/.config.yaml`. On GitHub, open the file and use **Raw** or **Download** to obtain the actual contents.

Your resulting structure should look like:

```text
xiaozhi-server/
├── docker-compose.yml
├── data/
│   └── .config.yaml
└── models/
    └── SenseVoiceSmall/
        └── model.pt
```

### 5. Configure the model provider

Update `data/.config.yaml` to supply the model API keys and selected modules. See [Configuration](#configuration) below. Do not publish secret keys or commit `.config.yaml` with live credentials.

### 6. Start the server

Open a terminal in the working directory and run:

```bash
docker compose up -d
docker logs -f xiaozhi-esp32-server
```

Review the logs as described under [Verify Server Startup](#verify-server-startup).

### 7. Upgrade an existing deployment

Back up `data/.config.yaml`, any locally stored data, and other persistent volumes. When upgrading, compare new configuration fields with your existing settings, and copy over **only your customized values** rather than replacing a new configuration file with an outdated one.

The original deployment workflow uses the following commands to remove old containers/images before redeployment. **Check that persistent database and data volumes are backed up before removing anything.**

```bash
docker stop xiaozhi-esp32-server
docker rm xiaozhi-esp32-server
docker stop xiaozhi-esp32-server-web
docker rm xiaozhi-esp32-server-web
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest
```

Then follow the Docker setup again using the desired image tag. Stopped or nonexistent containers may cause harmless command errors.

## Option 2. Run the source code locally

### 1. Prepare a Python environment

This project uses Conda to manage dependencies. Alternatively, install Python, `libopus`, and `ffmpeg` through your system package manager.

On Windows, install Anaconda and open **Anaconda Prompt**:

![Anaconda Prompt](images/conda_env_1.png)

![Conda environment](images/conda_env_2.png)

Create a Python 3.10 environment:

```bash
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server

# Optional China mirror channels
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge

conda install libopus -y
conda install ffmpeg -y

# On Linux, if libiconv.so.2 is missing
conda install libiconv -y
```

Check the output after each step. If you want to recreate an **existing** environment completely, `conda remove -n xiaozhi-esp32-server --all -y` will destroy that environment and its installed packages.

### 2. Download the project

Clone [Momo Companion Server](https://github.com/cloudymondaypm/momo-companion-server), or use GitHub's **Code → Download ZIP** option. In the cloned repository:

```bash
conda activate xiaozhi-esp32-server
cd main/xiaozhi-server

# Optional PyPI mirror
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt
```

### 3. Download the ASR model

Place `model.pt` inside `main/xiaozhi-server/models/SenseVoiceSmall/`, using the [download links](#model-files) below.

### 4. Configure the server

Create `main/xiaozhi-server/data/.config.yaml` and provide only the settings you want to override. See [Configuration](#configuration).

### 5. Start the server

```bash
# Run from main/xiaozhi-server
conda activate xiaozhi-esp32-server
python app.py
```

## Configuration

If the `data` directory does not exist, create it. You can either copy the full `config.yaml` to `data/.config.yaml`, or—preferably—create a minimal override file. The server reads `data/.config.yaml` first and falls back to `config.yaml` for unspecified values.

An example English-first configuration using the ChatGLM LLM adapter:

```yaml
prompt: |
  You are Momo Companion, a cheerful, helpful voice assistant.
  Respond naturally and concisely in the user's language.
  You can speak English, Filipino, or Chinese as appropriate.
  Do not include XML configuration tags in your spoken responses.

selected_module:
  LLM: ChatGLMLLM

LLM:
  ChatGLMLLM:
    api_key: YOUR_ZHIPU_API_KEY
```

Create your Zhipu API key through the [provider console](https://bigmodel.cn/usercenter/proj-mgmt/apikeys). If selecting a different model, change `selected_module.LLM` and configure the corresponding `LLM` entry. For full details, read [the server's default configuration](../main/xiaozhi-server/config.yaml).

## Model Files

The default offline speech recognizer is `SenseVoiceSmall`. Download `model.pt` and place it in `models/SenseVoiceSmall/` relative to the server's working directory.

- [ModelScope download](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt)
- [Baidu Netdisk alternative](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) (access code `qvna`)

## Verify Server Startup

The logs should show an OTA URL and WebSocket URL. A typical local setup uses:

```text
OTA:       http://192.168.1.25:8003/xiaozhi/ota/
WebSocket: ws://192.168.1.25:8000/xiaozhi/v1/
```

Do **not** open a WebSocket endpoint directly in a standard browser tab; use a WebSocket client or the `digital-human` test module. When running in Docker, the IP address displayed in the logs may be the container's internal IP and not reachable by your device. Use the host's LAN IP or properly configured public domain instead.

Once the server is working, either [build your own ESP32 firmware](firmware-build.md) or [point supported prebuilt firmware to your server](firmware-setting.md).

## Additional help

- [Frequently Asked Questions](FAQ.md)
- [Full-module deployment](Deployment_all.md)
- [MQTT gateway](mqtt-gateway-integration.md)
- [Home Assistant integration](homeassistant-integration.md)
- [Vision integration](mcp-vision-integration.md)
- [MCP endpoint](mcp-endpoint-enable.md)
- [Voiceprint recognition](voiceprint-integration.md)
- [Weather](weather-integration.md)
- [Web search](web-search-integration.md)
- [Performance benchmark](performance_tester.md)
