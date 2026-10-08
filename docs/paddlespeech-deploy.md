# Integrate PaddleSpeech TTS with Momo Companion

## Key considerations

**Advantages:** Can run offline and locally with low latency.

**Limitations:** As of September 25, 2025, the default model used by these instructions was Chinese-only. It does **not** reliably synthesize English sentences. For bilingual Chinese/English support, choose or train an appropriate multilingual model. The availability of newer models may differ.

## 1. Prerequisites

- Windows, Linux, or WSL2.
- Python 3.9 or newer, according to the version required by Paddle.
- A supported PaddlePaddle release: [official installation instructions](https://www.paddlepaddle.org.cn/install).
- Conda or a Python virtual environment.

## 2. Install and run PaddleSpeech

Clone the source:

```bash
git clone https://github.com/PaddlePaddle/PaddleSpeech.git
```

Create a Conda environment:

```bash
conda create -n paddle_env python=3.10 -y
conda activate paddle_env
```

Follow [PaddlePaddle installation instructions](https://www.paddlepaddle.org.cn/install) for your CPU or GPU. Then install PaddleSpeech using a compatible package source:

```bash
cd PaddleSpeech
pip install pytest-runner -i https://pypi.tuna.tsinghua.edu.cn/simple

# Choose the dependencies appropriate to your environment
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
pip install paddlespeech -i https://pypi.tuna.tsinghua.edu.cn/simple
```

To download a model automatically, run a test synthesis:

```bash
paddlespeech tts --input "你好，这是一次测试"
```

The model should download to your local `.paddlespeech/models` cache. The Chinese test phrase is intentional for the Chinese-only model.

Open `PaddleSpeech/demos/streaming_tts_server/conf/tts_online_application.yaml` and set `protocol` to `websocket`.

Start the streaming TTS service, adjusting the configuration path to your checkout:

```bash
paddlespeech_server start --config_file ./demos/streaming_tts_server/conf/tts_online_application.yaml
```

The server should report a successful startup and listen on an address such as `http://0.0.0.0:8092`.

## 3. Configure Momo Companion

Provider implementation: `main/xiaozhi-server/core/providers/tts/paddle_speech.py`.

In `main/xiaozhi-server/data/.config.yaml`, add:

```yaml
selected_module:
  TTS: PaddleSpeechTTS
TTS:
  PaddleSpeechTTS:
    type: paddle_speech
    protocol: websocket
    url: ws://127.0.0.1:8092/paddlespeech/tts/streaming
    spk_id: 0               # Default speaker
    sample_rate: 24000       # Output sample rate
    speed: 1.0               # Normal speech rate
    volume: 1.0              # Normal volume
    save_path:
```

Restart `xiaozhi-server`:

```bash
python app.py
```

Optionally start `main/digital-human` via `python start.py` and open `http://127.0.0.1:8006/index.html` to test text-to-speech requests. Inspect the PaddleSpeech logs for WebSocket connections and synthesis timings.

Example expected log events:

```text
INFO: WebSocket /paddlespeech/tts/streaming [accepted]
INFO: connection open
INFO: The durations of audio is: 2.4625 s
INFO: Complete the synthesis of the audio streams
INFO: connection closed
```

**Note:** If PaddleSpeech is hosted on a different machine, replace `127.0.0.1` with its reachable IP or hostname.
