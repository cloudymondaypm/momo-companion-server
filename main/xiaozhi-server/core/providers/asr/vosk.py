import os
import json
import time
from typing import Optional, Tuple, List
from .base import ASRProviderBase
from config.logger import setup_logging
from core.providers.asr.dto.dto import InterfaceType
import vosk

TAG = __name__
logger = setup_logging()

class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool = True):
        super().__init__()
        self.interface_type = InterfaceType.LOCAL
        self.model_path = config.get("model_path")
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file
        
        # Initialize VOSK model
        self.model = None
        self.recognizer = None
        self._load_model()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_model(self):
        """Load VOSK model"""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"VOSK model path does not exist: {self.model_path}")
                
            logger.bind(tag=TAG).info(f"Loading VOSK model: {self.model_path}")
            self.model = vosk.Model(self.model_path)

            # Initialize VOSK recognizer (sample rate must be 16 kHz)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)

            logger.bind(tag=TAG).info("VOSK model loaded successfully")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to load VOSK model: {e}")
            raise

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, artifacts=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Transcribe audio to text"""
        try:
            # Check if model loaded successfully
            if not self.model:
                logger.bind(tag=TAG).error("VOSK model is not loaded; cannot transcribe")
                return "", None
            
            if artifacts is None:
                return "", None
            if not artifacts.pcm_bytes:
                logger.bind(tag=TAG).warning("Combined PCM data is empty")
                return "", None

            start_time = time.time()
            
            
            # Transcribe audio (VOSK recommends chunks of 2,000 bytes)
            chunk_size = 2000
            text_result = ""
            
            for i in range(0, len(artifacts.pcm_bytes), chunk_size):
                chunk = artifacts.pcm_bytes[i:i+chunk_size]
                if self.recognizer.AcceptWaveform(chunk):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '')
                    if text:
                        text_result += text + " "
            
            # Get final result
            final_result = json.loads(self.recognizer.FinalResult())
            final_text = final_result.get('text', '')
            if final_text:
                text_result += final_text
            
            logger.bind(tag=TAG).debug(
                f"VOSK ASR duration: {time.time() - start_time:.3f}s | Result: {text_result.strip()}"
            )
            
            return text_result.strip(), artifacts.file_path
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"VOSK ASR failed: {e}")
            return "", None
