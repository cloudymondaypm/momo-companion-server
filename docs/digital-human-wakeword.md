# Digital Human Wake-Word Runtime Setup

## Overview

The test page uses Sherpa-ONNX for lightweight, low-latency wake-word detection. It supports custom wake words and real-time listening.

## Wake-Word Model

### Download model files (required)

**Important:** The model files are not included in this repository and must be downloaded separately.

### Official model sources

- **Official model list**: <https://csukuangfj.github.io/sherpa/onnx/kws/pretrained_models/index.html>
- **Recommended model**: `sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01`

### Download and configuration

#### 1. Download the model archive

```bash
# Method 1: Direct download (recommended)
cd main/digital-human/wakeword_runtime/
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01.tar.bz2

# Extract
tar xvf sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01.tar.bz2

# Method 2: Use ModelScope
pip install modelscope
python -c "
from modelscope import snapshot_download
snapshot_download('pkufool/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01', cache_dir='./models')
"
```

#### 2. Set up model files

The model archive contains the following files:

```
sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/
├── encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx    # Optimized for speed
├── encoder-epoch-12-avg-2-chunk-16-left-64.onnx
├── encoder-epoch-99-avg-1-chunk-16-left-64.int8.onnx    # Optimized for speed
├── encoder-epoch-99-avg-1-chunk-16-left-64.onnx         # Optimized for accuracy
├── decoder-epoch-12-avg-2-chunk-16-left-64.onnx
├── decoder-epoch-99-avg-1-chunk-16-left-64.onnx         # Optimized for accuracy
├── joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx     # Optimized for speed
├── joiner-epoch-12-avg-2-chunk-16-left-64.onnx
├── joiner-epoch-99-avg-1-chunk-16-left-64.int8.onnx     # Optimized for speed
├── joiner-epoch-99-avg-1-chunk-16-left-64.onnx          # Optimized for accuracy
├── tokens.txt                    # Token mapping (required)
├── keywords_raw.txt              # May be included (optional; not required by runtime)
├── keywords.txt                  # Ready-to-use
├── test_wavs/                    # Test audio (optional)
├── configuration.json            # Model metadata (optional)
└── README.md                     # Documentation (optional)
```

#### 3. Choose model variant

**Option 1: Prioritize accuracy (recommended)**

```bash
cd sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01

# Create model directory
mkdir -p ../models

# Copy the epoch-99 FP32 encoder, decoder and joiner
cp encoder-epoch-99-avg-1-chunk-16-left-64.onnx ../models/encoder.onnx
cp decoder-epoch-99-avg-1-chunk-16-left-64.onnx ../models/decoder.onnx
cp joiner-epoch-99-avg-1-chunk-16-left-64.onnx ../models/joiner.onnx

# Copy supporting files
cp tokens.txt ../models/tokens.txt
# Keep keywords_raw.txt if provided; it is not required by the runtime
```

**Option 2: Prioritize speed**

```bash
cd sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01

# Create model directory
mkdir -p ../models

# Copy the epoch-99 INT8 encoder, decoder and joiner
cp encoder-epoch-99-avg-1-chunk-16-left-64.int8.onnx ../models/encoder.onnx
cp decoder-epoch-99-avg-1-chunk-16-left-64.onnx ../models/decoder.onnx
cp joiner-epoch-99-avg-1-chunk-16-left-64.int8.onnx ../models/joiner.onnx

# Copy supporting files
cp tokens.txt ../models/tokens.txt
```

**Important notes**:

- **Do not mix FP32 and INT8 weights:** all three model files should use compatible precision
- **Prefer epoch-99** if prioritizing model quality over other tradeoffs
- **Required files**：`encoder.onnx` + `decoder.onnx` + `joiner.onnx` + `tokens.txt` + `keywords.txt`

### Final model directory

Place the configured files in `wakeword_runtime/models/` with full path `main/digital-human/wakeword_runtime/models/`：

```
wakeword_runtime/models/
├── encoder.onnx      # Renamed encoder model
├── decoder.onnx      # Renamed decoder model
├── joiner.onnx       # Renamed joiner model
├── tokens.txt        # Pinyin token map (228-line version)
├── keywords.txt      # Wake-word keywords file (generated on first startup)
└── keywords_raw.txt  # Optional; not required by runtime
```

## Start the runtime

From the `main/digital-human` directory, run:

```bash
pip install -r wakeword_runtime/requirements.txt
python start.py
```

Default endpoints：

- Web page：`http://127.0.0.1:8006/index.html`
- Event bridge：`ws://127.0.0.1:8006/wakeword-ws`
- Health check：`http://127.0.0.1:8006/health`

To stop：

- Press `Ctrl+C`
- This stops the page server, event bridge and wake-word detector

## Configuration reference

Configuration file: [main/digital-human/wakeword_runtime/config.json](../main/digital-human/wakeword_runtime/config.json)。

Main settings:：

```json
{
  "wakeword": {
    "enabled": true
  },
  "model_dir": "models",
  "audio": {
    "input_device": null,
    "sample_rate": 16000,
    "channels": 1
  },
  "detector": {
    "num_threads": 4,
    "provider": "cpu",
    "max_active_paths": 2,
    "keywords_score": 1.8,
    "keywords_threshold": 0.1,
    "num_trailing_blanks": 1,
    "cooldown_seconds": 1.5
  },
  "logging": {
    "level": "INFO",
    "dir": "logs",
    "file": "wakeword-runtime.log"
  }
}
```

Configuration fields：

| Parameter | Description |
| --- | --- |
| `wakeword.enabled` | Enable local wake-word detection |
| `model_dir` | Model and vocabulary directory |
| `audio.input_device` | Microphone input device; defaults to system device |
| `audio.sample_rate` | Sample rate, default `16000` |
| `audio.channels` | Audio channels, default `1` |
| `detector.num_threads` | Detector threads |
| `detector.provider` | Inference provider; usually `cpu` |
| `detector.max_active_paths` | Number of search paths |
| `detector.keywords_score` | Keyword boosting score |
| `detector.keywords_threshold` | Detection threshold |
| `detector.num_trailing_blanks` | Number of trailing blanks |
| `detector.cooldown_seconds` | Cooldown between detections |
| `logging.level` | Log level |
| `logging.dir` | Log directory |
| `logging.file` | Log filename |

## Recommended workflow

### First use

1. Prepare `models/` model files and `tokens.txt`
2. Verify `models/keywords.txt` exists
3. From the `digital-human` directory, run `python start.py`
4. Open in a browser `http://127.0.0.1:8006/index.html`
5. Check wake-word settings on the configuration page

### Change wake words

1. Open the digital-human settings page
2. Open the Wake Word tab
3. Update the enabled state or list of wake words
4. Click Apply Wake Words
5. Follow prompts to restart if necessary

### Disable wake-word detection

1. Disable Local Wake Words
2. Click Apply Wake Words
3. Restart to apply changes

When disabled：

- The web page and event bridge remain available
- Wake-word detection stops
