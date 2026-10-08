# IndexStreamTTS Integration Guide

## Environment Preparation
### 1. Clone the project 
```bash 
git clone https://github.com/Ksuriuri/index-tts-vllm.git
```
Enter the cloned directory
```bash
cd index-tts-vllm
```
Switch to the pinned commit compatible with vLLM 0.10.2
```bash
git checkout 224e8d5e5c8f66801845c66b30fa765328fd0be3
```

### 2. Create and activate the Conda environment
```bash 
conda create -n index-tts-vllm python=3.12
conda activate index-tts-vllm
```

### 3. Install PyTorch 2.8.0 for the pinned vLLM version
#### Check the supported CUDA version and installed CUDA compiler
```bash
nvidia-smi
nvcc --version
``` 
#### Maximum CUDA version reported by the driver
```bash
CUDA Version: 12.8
```
#### Installed CUDA compiler version
```bash
Cuda compilation tools, release 12.8, V12.8.89
```
#### Example installation command for CUDA 12.8
```bash
pip install torch torchvision
```
Use PyTorch 2.8.0 for vLLM 0.10.2; check exact commands at：[the PyTorch website](https://pytorch.org/get-started/locally/)

### 4. Install dependencies
```bash 
pip install -r requirements.txt
```

### 5. Download model weights
### Option 1: Download official weights and convert
Download official weights to any local path. IndexTTS-1.5 is supported.  
| HuggingFace                                                   | ModelScope                                                          |
|---------------------------------------------------------------|---------------------------------------------------------------------|
| [IndexTTS](https://huggingface.co/IndexTeam/Index-TTS)        | [IndexTTS](https://modelscope.cn/models/IndexTeam/Index-TTS)        |
| [IndexTTS-1.5](https://huggingface.co/IndexTeam/IndexTTS-1.5) | [IndexTTS-1.5](https://modelscope.cn/models/IndexTeam/IndexTTS-1.5) |

Example using ModelScope:  
#### Ensure Git LFS is installed and initialized
```bash
sudo apt-get install git-lfs
git lfs install
```
Create a model directory and download the weights
```bash 
mkdir model_dir
cd model_dir
git clone https://www.modelscope.cn/IndexTeam/IndexTTS-1.5.git
```

#### Convert the weights
```bash 
bash convert_hf_format.sh /path/to/your/model_dir
```
For example, if IndexTTS-1.5 is in model_dir, run:
```bash
bash convert_hf_format.sh model_dir/IndexTTS-1.5
```
This converts official weights into a Transformers-compatible representation under the model's vllm subdirectory.

### 6. Adapt the API response for this project
The example API needs to return raw audio to match the Momo server's TTS adapter.
```bash
vi api_server.py
```
```bash 
@app.post("/tts", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api(request: Request):
    try:
        data = await request.json()
        text = data["text"]
        character = data["character"]

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, text)

        return Response(content=wav.tobytes(), media_type="application/octet-stream")
        
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        print(tb_str)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )
```

### 7. Write a startup script (run it in the matching Conda environment)
```bash 
vi start_api.sh
```
### Paste the following into the file and save with `:wq`  
#### Replace /home/system/index-tts-vllm/model_dir/IndexTTS-1.5 with your real model path
```bash
# Activate Conda environment
conda activate index-tts-vllm 
echo "Activated the project Conda environment"
sleep 2
# Find process using TCP port 11996
PID_VLLM=$(sudo netstat -tulnp | grep 11996 | awk '{print $7}' | cut -d'/' -f1)

# Check whether a process was found
if [ -z "$PID_VLLM" ]; then
  echo "No process is listening on port 11996"
else
  echo "Process using port 11996: $PID_VLLM"
  # Try graceful termination first, then wait two seconds
  kill $PID_VLLM
  sleep 2
  # Check if process is still running
  if ps -p $PID_VLLM > /dev/null; then
    echo "Process is still running; forcing termination..."
    kill -9 $PID_VLLM
  fi
  echo "Stopped process $PID_VLLM"
fi

# Find VLLM/EngineCore processes
GPU_PIDS=$(ps aux | grep -E "VLLM|EngineCore" | grep -v grep | awk '{print $2}')

# Check whether a process was found
if [ -z "$GPU_PIDS" ]; then
  echo "No VLLM-related processes found"
else
  echo "VLLM-related process IDs: $GPU_PIDS"
  # Try graceful termination first, then wait two seconds
  kill $GPU_PIDS
  sleep 2
  # Check if process is still running
  if ps -p $GPU_PIDS > /dev/null; then
    echo "Process is still running; forcing termination..."
    kill -9 $GPU_PIDS
  fi
  echo "Stopped process $GPU_PIDS"
fi

# Create tmp directory if missing
mkdir -p tmp

# Start api_server.py in the background and redirect output
nohup python api_server.py --model_dir /home/system/index-tts-vllm/model_dir/IndexTTS-1.5 --port 11996 > tmp/server.log 2>&1 &
echo "api_server.py is running in the background; see tmp/server.log"
```
Make the script executable and run it
```bash 
chmod +x start_api.sh
./start_api.sh
```
View service logs in tmp/server.log:
```bash
tail -f tmp/server.log
```
If enough GPU memory is available, adjust the `--gpu_memory_utilization` argument (default 0.25).

## Voice Configuration
index-tts-vllm supports custom and mixed voices registered through a configuration file.  
Register custom speakers in assets/speaker.json at the project root.
### Configuration format
```bash
{
    "speaker_name_1": [
        "audio_file_1.wav",
        "audio_file_2.wav"
    ],
    "speaker_name_2": [
        "audio_file_3.wav"
    ]
}
```
### Note: Restart the service to register voices after editing agent settings
In the management console add the speaker after restarting; for standalone deployments, select the corresponding voice.