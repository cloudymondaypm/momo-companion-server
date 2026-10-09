import time
import json
import uuid
import random
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.wakeup_word import WakeupWordsConfig
from core.handle.sendAudioHandle import sendAudioMessage, send_tts_message
from core.utils.util import remove_punctuation_and_length, opus_datas_to_wav_bytes
from core.providers.tools.device_mcp import MCPClient, send_mcp_initialize_message

TAG = __name__

WAKEUP_CONFIG = {
    "refresh_time": 10,
    "responses": [
        "I'm right here. Go ahead!",
        "I'm here whenever you need me.",
        "Coming! What's on your mind?",
        "Go ahead, I'm listening.",
        "I'm ready whenever you are.",
        "Tell me what you'd like to do.",
        "I'm all ears!",
        "How can I help you?",
        "I'm here, ready to help.",
    ],
}

# Create global wake-word configuration manager
wakeup_words_config = WakeupWordsConfig()

# Lock to prevent concurrent wakeupWordsResponse calls
_wakeup_response_lock = asyncio.Lock()


async def handleHelloMessage(conn: "ConnectionHandler", msg_json):
    """Handle hello message"""
    audio_params = msg_json.get("audio_params")
    if audio_params:
        format = audio_params.get("format")
        conn.logger.bind(tag=TAG).debug(f"Client audio format: {format}")
        conn.audio_format = format
        conn.welcome_msg["audio_params"] = audio_params
    features = msg_json.get("features")
    if features:
        conn.logger.bind(tag=TAG).debug(f"Client capabilities: {features}")
        conn.features = features
        if features.get("mcp"):
            conn.logger.bind(tag=TAG).debug("Client supports MCP")
            conn.mcp_client = MCPClient()
        if features.get("aec"):
            conn.logger.bind(tag=TAG).debug("Client enabled server-side AEC")
            conn.client_aec = True

    await conn.websocket.send(json.dumps(conn.welcome_msg))

    # The device waits for the server hello before processing MCP messages.
    if features and features.get("mcp"):
        asyncio.create_task(send_mcp_initialize_message(conn))


async def checkWakeupWords(conn: "ConnectionHandler", text):
    enable_wakeup_words_response_cache = conn.config[
        "enable_wakeup_words_response_cache"
    ]

    # Wait up to three seconds for TTS initialization
    start_time = time.time()
    while time.time() - start_time < 3:
        if conn.tts:
            break
        await asyncio.sleep(0.1)
    else:
        return False

    if not enable_wakeup_words_response_cache:
        return False

    _, filtered_text = remove_punctuation_and_length(text)
    if filtered_text not in conn.config.get("wakeup_words"):
        return False

    conn.just_woken_up = True
    await send_tts_message(conn, "start")

    # Get current voice
    voice = getattr(conn.tts, "voice", "default")
    if not voice:
        voice = "default"

    # Get wake-word response configuration
    response = wakeup_words_config.get_wakeup_response(voice)
    if not response or not response.get("file_path"):
        response = {
            "voice": "default",
            "file_path": "config/assets/wakeup_words_short.wav",
            "time": 0,
            "text": "I'm here!",
        }

    # Get audio data
    opus_packets = await audio_to_data(response.get("file_path"), use_cache=False)
    # Play wake-word response
    conn.client_abort = False

    # Treat wake-word reply as a new session with a fresh sentence_id to reset flow control
    conn.sentence_id = str(uuid.uuid4().hex)

    conn.logger.bind(tag=TAG).info(f"Play wake-word response: {response.get('text')}")
    await sendAudioMessage(conn, SentenceType.FIRST, opus_packets, response.get("text"))
    await sendAudioMessage(conn, SentenceType.LAST, [], None)

    # Append to conversation
    conn.dialogue.put(Message(role="assistant", content=response.get("text")))

    # Check whether wake-word response needs updating
    if time.time() - response.get("time", 0) > WAKEUP_CONFIG["refresh_time"]:
        if not _wakeup_response_lock.locked():
            asyncio.create_task(wakeupWordsResponse(conn))
    return True


async def wakeupWordsResponse(conn: "ConnectionHandler"):
    if not conn.tts:
        return

    try:
        # Acquire lock if available; otherwise return
        if not await _wakeup_response_lock.acquire():
            return

        # Select a random predefined reply
        result = random.choice(WAKEUP_CONFIG["responses"])
        if not result or len(result) == 0:
            return

        # Generate TTS audio
        tts_result = await asyncio.to_thread(conn.tts.to_tts, result)
        if not tts_result:
            return

        # Get current voice
        voice = getattr(conn.tts, "voice", "default")

        # Use the connection's sample rate
        wav_bytes = opus_datas_to_wav_bytes(tts_result, sample_rate=conn.sample_rate)
        file_path = wakeup_words_config.generate_file_path(voice)
        with open(file_path, "wb") as f:
            f.write(wav_bytes)
        # Update configuration
        wakeup_words_config.update_wakeup_response(voice, file_path, result)
    finally:
        # Always release the lock
        if _wakeup_response_lock.locked():
            _wakeup_response_lock.release()
