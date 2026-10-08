# Frequently Asked Questions ❓

### 1. Why is my speech transcribed as Korean, Japanese, or English when I speak Chinese?

Check that `models/SenseVoiceSmall/model.pt` exists. If it does not, download the speech-recognition model following the [deployment guide](Deployment.md). You can also check the ASR language settings to prevent short utterances from being misidentified.

### 2. Why do I receive a "TTS task error: file not found"?

Confirm that `libopus` and `ffmpeg` were installed correctly into your Conda environment. If either is missing, install it:

```bash
conda install conda-forge::libopus
conda install conda-forge::ffmpeg
```

### 3. Why does TTS frequently fail or time out?

If EdgeTTS frequently fails, check whether your network is using a proxy. Try temporarily disabling the proxy to see whether it is responsible.

If you use Volcengine Doubao TTS, consider a paid tier for production. The trial version may allow only two simultaneous sessions, which can cause request failures under load.

### 4. My device connects to the self-hosted server over Wi-Fi, but not over 4G.

Some Xiaozhi firmware requires a secure connection when using 4G. You can either change the firmware as demonstrated in [this video](https://www.bilibili.com/video/BV18MfTYoE85) or configure HTTPS/WSS with an SSL certificate through Nginx, as described in [this guide](https://icnt94i5ctj4.feishu.cn/docx/GnYOdMNJOoRCljx1ctecsj9cnRe).

### 5. How can I improve Momo Companion response times?

The project defaults are designed to minimize costs. Start with the free models to verify a working deployment, then optimize latency. Since version 0.5.2, streaming configurations have improved response time by approximately 2.5 seconds compared with earlier versions, based on the upstream project's findings.

| Component | Free starter configuration | Example streaming configuration |
| --- | --- | --- |
| ASR (speech recognition) | FunASR (local) | XunfeiStreamASR (streaming) |
| LLM | glm-4-flash (Zhipu) | qwen-flash (Alibaba Bailian) |
| VLLM (vision) | glm-4v-flash (Zhipu) | qwen3.5-flash (Alibaba Bailian) |
| TTS | EdgeTTS (Microsoft) | HuoshanDoubleStreamTTS (Volcengine) |
| Intent recognition | function_call | function_call |
| Memory | mem_local_short | mem_local_short |

Actual availability, pricing, and speed depend on your provider and deployment region. For benchmarking methods, see the [upstream component performance report](https://github.com/xinnan-tech/xiaozhi-performance-research).

### 6. The assistant interrupts me whenever I pause. How can I fix this?

Increase `min_silence_duration_ms` in your server configuration, for example to `1000`, so the VAD waits longer before ending your turn:

```yaml
VAD:
  SileroVAD:
    threshold: 0.5
    model_dir: models/snakers4_silero-vad
    min_silence_duration_ms: 1000  # Increase for longer speaking pauses
```

### 7. Deployment guides

1. [Minimal deployment](./Deployment.md)
2. [Full-module deployment](./Deployment_all.md)
3. [MQTT gateway and MQTT+UDP](./mqtt-gateway-integration.md)
4. [Automatic pull, build, and startup](./dev-ops-integration.md)
5. [Nginx integration](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791)
6. [Build your own Docker image](./docker-build.md)

### 8. Firmware guides

1. [Build ESP32 firmware](./firmware-build.md)
2. [Change the OTA address in prebuilt firmware](./firmware-setting.md)
3. [Set up firmware OTA upgrades in a single-module deployment](./ota-upgrade-guide.md)

### 9. Integrations and extensions

1. [Phone-number registration for the management console](./ali-sms-integration.md)
2. [Home Assistant smart home integration](./homeassistant-integration.md)
3. [Vision and photo recognition](./mcp-vision-integration.md)
4. [Deploy an MCP endpoint](./mcp-endpoint-enable.md)
5. [Connect to an MCP endpoint](./mcp-endpoint-integration.md)
6. [Read device information from an MCP function](./mcp-get-device-info.md)
7. [Voiceprint recognition](./voiceprint-integration.md)
8. [News provider configuration](./newsnow_plugin_config.md)
9. [RAGFlow knowledge base integration](./ragflow-integration.md)
10. [Context provider integration](./context-provider-integration.md)
11. [PowerMem memory integration](./powermem-integration.md)
12. [Weather plugin](./weather-integration.md)
13. [Device-to-device calling](./device-call-guide.md)
14. [Web search](./web-search-integration.md)

### 10. Digital human guides

1. [Start the digital human](./digital-human-wakeword.md)
2. [Deploy the digital human on an N100 mini PC](./all-in-one-digital-human-setup.md)

### 11. Voice cloning and local TTS

1. [Clone voices in the management console](./huoshan-streamTTS-voice-cloning.md)
2. [Integrate Index-TTS](./index-stream-integration.md)
3. [Integrate Fish Speech](./fish-speech-integration.md)
4. [Integrate PaddleSpeech](./paddlespeech-deploy.md)

### 12. Performance tests

1. [Component benchmark guide](./performance_tester.md)
2. [Published upstream benchmark results](https://github.com/xinnan-tech/xiaozhi-performance-research)

### 13. Where can I report problems?

Please [open an issue in the Momo Companion repository](https://github.com/cloudymondaypm/momo-companion-server/issues). For upstream-related issues, you may also consult [the upstream issue tracker](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues).
