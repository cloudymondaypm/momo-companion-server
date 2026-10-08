# Deploy Fish Speech for Momo Companion

## 1. Prepare the AutoDL instance

Sign in to [AutoDL](https://autodl.com/console/instance/list), rent an instance, and select an image comparable to:

```text
PyTorch / 2.1.0 / Python 3.10 (Ubuntu 22.04) / CUDA 12.1
```

After the instance starts, enable the optional network accelerator if provided:

```bash
source /etc/network_turbo
```

Open your working directory:

```bash
cd autodl-tmp/
```

Clone Fish Speech:

```bash
git clone https://gitclone.com/github.com/fishaudio/fish-speech.git
cd fish-speech
```

Install the project:

```bash
pip install -e .
```

If dependencies fail due to missing PortAudio headers, install them:

```bash
apt-get install portaudio19-dev -y
```

Install the matching PyTorch packages for CUDA 12.1 when required:

```bash
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
```

## 2. Download models and start the API

```bash
cd tools
python download_models.py
python -m tools.api_server --listen 0.0.0.0:6006
```

## 3. Configure port forwarding

Open the [AutoDL instance console](https://autodl.com/console/instance/list), select your instance's **Custom Service** option, and enable forwarding for port `6006`.

![AutoDL Custom Service](images/fishspeech/autodl-01.png)

After forwarding, visit `http://localhost:6006/` from your computer to verify the Fish Speech API.

![API preview](images/fishspeech/autodl-02.png)

## 4. Configure standalone xiaozhi-server

Set the TTS provider in `data/.config.yaml`:

```yaml
selected_module:
  TTS: FishSpeech
TTS:
  FishSpeech:
    reference_audio: ["config/assets/wakeup_words.wav"]
    reference_text: ["哈啰啊，我是小智啦，声音好听的台湾女孩一枚，超开心认识你耶，最近在忙啥，别忘了给我来点有趣的料哦，我超爱听八卦的啦"]
    api_key: "123"
    api_url: "http://127.0.0.1:6006/v1/tts"
```

The sample reference text is intentionally Chinese because it matches the original Chinese reference-audio recording. If you use an English voice recording, replace **both** the audio and text with a matching English reference.

Restart the server for the change to take effect. Replace localhost with the reachable API address when Fish Speech runs on another machine.
