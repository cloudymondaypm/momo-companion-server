# Frequently Asked Questions ❓

### 1. Why does the assistant transcribe my speech as Korean, Japanese, or English when I speak Chinese? 🇰🇷

**Recommendation:** Verify that `models/SenseVoiceSmall/model.pt` exists. If it does not, download the speech recognition model as described in [Download Speech Recognition Model Files](Deployment.md#模型文件).

### 2. Why do I get "TTS task failed: file not found"? 📁

Check that `libopus` and `ffmpeg` were installed correctly with Conda. Install them if missing:

```bash
conda install conda-forge::libopus
conda install conda-forge::ffmpeg
```

### 3. TTS frequently fails or times out ⏰

If `EdgeTTS` frequently fails, check whether you're using a proxy or VPN; try disabling the proxy and retry. With Volcengine Doubao TTS, a paid tier may be more reliable, since its trial tier has a low concurrency limit (historically two concurrent requests).

### 4. The self-hosted server works over Wi-Fi, but not over 4G 🔐

**Cause:** The referenced Xiaozhi device firmware requires a secure connection over its 4G mode.

**Possible fixes:**

1. Modify the firmware using [this video guide](https://www.bilibili.com/video/BV18MfTYoE85).
2. Configure an SSL certificate with Nginx using [this guide](https://icnt94i5ctj4.feishu.cn/docx/GnYOdMNJOoRCljx1ctecsj9cnRe).

### 5. How can I improve Momo Companion's response time? ⚡

The project defaults to low-cost settings. First get a working assistant using the free models, then optimize latency. Since version `0.5.2`, streaming configurations can improve responsiveness; upstream reported approximately 2.5 seconds of improvement over older versions.

| Component | Free starter configuration | Streaming alternative |
|:---:|:---:|:---:|
| ASR (speech recognition) | FunASR (local) | XunfeiStreamASR (iFlytek) |
| LLM (language model) | glm-4-flash (Zhipu) | qwen-flash (Alibaba Bailian) |
| VLLM (vision model) | glm-4v-flash (Zhipu) | qwen3.5-flash (Alibaba Bailian) |
| TTS (speech synthesis) | EdgeTTS (Microsoft) | HuoshanDoubleStreamTTS (Volcengine) |
| Intent recognition | function_call | function_call |
| Memory | mem_local_short (local short-term memory) | mem_local_short |

For component latency, see the [Xiaozhi Performance Research project](https://github.com/xinnan-tech/xiaozhi-performance-research) and test using its methodology in your own environment.

### 6. I speak slowly, and Momo keeps interrupting me 🗣️

Increase `min_silence_duration_ms` in your VAD configuration (for example, to `1000`):

```yaml
VAD:
  SileroVAD:
    threshold: 0.5
    model_dir: models/snakers4_silero-vad
    min_silence_duration_ms: 700  # Increase for longer pauses
```

### 7. Deployment tutorials

1. [Simplified deployment](./Deployment.md)
2. [Full-module deployment](./Deployment_all.md)
3. [MQTT gateway / MQTT+UDP setup](./mqtt-gateway-integration.md)
4. [Automatic code updates, build and startup](./dev-ops-integration.md)
5. [Nginx integration](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791)
6. [Building a custom Docker image](./docker-build.md)

### 8. Firmware build tutorials

1. [Build Xiaozhi firmware yourself](./firmware-build.md)
2. [Modify the OTA URL in existing firmware](./firmware-setting.md)
3. [Configure automatic firmware OTA updates in single-module deployments](./ota-upgrade-guide.md)

### 9. Extension and integration tutorials

1. [Enable phone-number registration](./ali-sms-integration.md)
2. [Home Assistant integration](./homeassistant-integration.md)
3. [Vision model for image recognition](./mcp-vision-integration.md)
4. [Deploy an MCP endpoint](./mcp-endpoint-enable.md)
5. [Integrate an MCP endpoint](./mcp-endpoint-integration.md)
6. [Retrieve device information using MCP tools](./mcp-get-device-info.md)
7. [Voiceprint recognition](./voiceprint-integration.md)
8. [News plugin feed configuration](./newsnow_plugin_config.md)
9. [RAGFlow knowledge base integration](./ragflow-integration.md)
10. [Context providers](./context-provider-integration.md)
11. [PowerMem intelligent memory](./powermem-integration.md)
12. [Weather plugin configuration](./weather-integration.md)
13. [Device-to-device calling](./device-call-guide.md)
14. [Web search integration](./web-search-integration.md)

### 10. Digital human tutorials

1. [Start the digital-human module](./digital-human-wakeword.md)
2. [Deploy digital-human on an N100 mini PC](./all-in-one-digital-human-setup.md)

### 11. Voice cloning and local TTS tutorials

1. [Clone a voice in the management console](./huoshan-streamTTS-voice-cloning.md)
2. [Deploy local Index-TTS](./index-stream-integration.md)
3. [Deploy local Fish Speech](./fish-speech-integration.md)
4. [Deploy local PaddleSpeech](./paddlespeech-deploy.md)

### 12. Performance testing

1. [Component performance testing guide](./performance_tester.md)
2. [Published performance research](https://github.com/xinnan-tech/xiaozhi-performance-research)

### 13. More questions 💬

You can open an issue in the [upstream repository](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues).
