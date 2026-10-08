# Enable Vision and Camera Recognition

This guide covers vision model activation in either a standalone server or a full management-console deployment.

## Prerequisites

- A camera-enabled ESP32 device whose firmware supports camera tools, for example the Lichuang ESP32-S3 development board supported by upstream Xiaozhi firmware.
- Device firmware **1.6.6 or newer**, according to the upstream integration guide.
- A working voice conversation between the device and your server.
- A supported vision-language model and its API credentials.

## Option 1. Standalone xiaozhi-server

### 1. Check network access

The vision HTTP endpoint normally runs on port `8003`. If using Docker, ensure `docker-compose.yml` publishes port `8003`. For source installations, allow the port through the host firewall.

### 2. Choose a vision model

Edit `data/.config.yaml` and configure `selected_module.VLLM` using a compatible vision-language model. The upstream example uses `ChatGLMVLLM`:

```yaml
selected_module:
  VLLM: ChatGLMVLLM

VLLM:
  ChatGLMVLLM:
    api_key: YOUR_ZHIPU_API_KEY
```

Get a key from the [Zhipu AI console](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) or reuse an existing one. Merge these keys into your existing YAML mappings and preserve other selected modules (VAD, ASR, LLM, TTS, Memory, Intent).

### 3. Restart the server

From source:

```bash
python app.py
```

With Docker:

```bash
docker restart xiaozhi-esp32-server
```

Look for a vision endpoint in the startup logs, such as:

```text
Vision analysis endpoint: http://192.168.4.7:8003/mcp/vision/explain
WebSocket endpoint:       ws://192.168.4.7:8000/xiaozhi/v1/
```

Open the vision URL in a browser or run:

```bash
curl -i http://192.168.4.7:8003/mcp/vision/explain
```

The response should indicate that the vision endpoint is available.

### 4. Set a reachable device-facing URL

For Docker and internet-facing deployments, explicitly configure `server.vision_explain` so the address sent to devices is **reachable by the device**, not a container-internal address:

```yaml
server:
  vision_explain: http://your-reachable-host:8003/mcp/vision/explain
```

Use HTTPS and a public domain where appropriate, or an accessible LAN address for local devices. A device outside your LAN cannot reach a private LAN or Docker-only IP.

### 5. Test from the device

Wake Momo Companion and ask: **"Open the camera and tell me what you see."** Review server logs for vision API or camera errors.

## Option 2. Full management-console deployment

### 1. Check networking and configuration

Make sure `docker-compose_all.yml` publishes port `8003`, or open that port if running from source. Confirm `data/.config.yaml` has the expected `config_from_api.yaml` structure for your full deployment.

### 2. Configure the vision model

1. Obtain an API key from the [Zhipu AI console](https://bigmodel.cn/usercenter/proj-mgmt/apikeys).
2. In the management console, open **Model Configuration → Vision-Language Models**.
3. Find `VLLM_ChatGLMVLLM` and enter your key under **API Key**.
4. Open the target agent's **Agent Configuration** and select the same vision-language model in **VLLM**. Save.

### 3. Restart and verify

```bash
# For source-based setup
python app.py

# Or, for Docker
docker restart xiaozhi-esp32-server
```

Check the vision endpoint and configure `server.vision_explain` as explained under [Option 1](#4-set-a-reachable-device-facing-url). Then ask the device to capture an image and describe it.
