import asyncio
import time
import numpy as np
from faster_whisper import WhisperModel
from typing import Optional, Tuple, List
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

class ASRProvider(ASRProviderBase):
    """CPU Faster-Whisper ASR with English/Filipino auto detection."""
    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        self.interface_type = InterfaceType.LOCAL
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file
        configured_model = config.get("model_dir", "models/faster-whisper-small")
        # Older database rows may point at a vanished Hugging Face cache snapshot.
        # Prefer the stable deployment path when that persisted model is mounted.
        persistent_model = "/opt/xiaozhi-esp32-server/models/faster-whisper-small"
        model_dir = persistent_model if __import__("os").path.isfile(
            __import__("os").path.join(persistent_model, "model.bin")
        ) else configured_model
        self.model = WhisperModel(
            model_dir,
            device=config.get("device", "cpu"),
            compute_type=config.get("compute_type", "int8"),
        )

    async def speech_to_text(self, opus_data: List[bytes], session_id: str, artifacts=None) -> Tuple[Optional[str], Optional[str]]:
        if artifacts is None:
            return "", None
        start = time.time()
        segments, info = await asyncio.to_thread(
            self.model.transcribe,
            np.frombuffer(artifacts.pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0,
            language=None,
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segments if s.text.strip()).strip()
        lang = info.language or ""
        if lang == "tl":
            lang = "fil"
        result = {"content": text, "language": lang, "emotion": "😶"}
        logger.bind(tag=TAG).info(f"Whisper ASR {time.time()-start:.3f}s [{lang}]: {text}")
        return result, artifacts.file_path
