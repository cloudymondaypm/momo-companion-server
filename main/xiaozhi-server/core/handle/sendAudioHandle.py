import json
import time
import asyncio
import opuslib_next
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils import textUtils
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.audioRateController import AudioRateController

TAG = __name__
# Audio frame duration (milliseconds)
AUDIO_FRAME_DURATION = 60
# Number of prebuffered packets sent immediately to reduce latency
PRE_BUFFER_COUNT = 5


async def sendAudioMessage(conn: "ConnectionHandler", sentenceType, audios, text, sentence_id=None):
    # Skip leftover audio from previous sentence
    if sentence_id is not None and sentence_id != conn.sentence_id:
        return

    if conn.tts.tts_audio_first_sentence:
        conn.logger.bind(tag=TAG).info(f"Sending first speech segment: {text}")
        conn.tts.tts_audio_first_sentence = False

    if sentenceType == SentenceType.FIRST:
        # Queue subsequent segments of the same sentence for rate control; otherwise send immediately
        if (
            hasattr(conn, "audio_rate_controller")
            and conn.audio_rate_controller
            and getattr(conn, "audio_flow_control", {}).get("sentence_id")
            == conn.sentence_id
        ):
            conn.audio_rate_controller.add_message(
                lambda: send_tts_message(conn, "sentence_start", text)
            )
        else:
            # Send immediately when starting a new sentence or rate controller is uninitialized
            await send_tts_message(conn, "sentence_start", text)

    await sendAudio(conn, audios)
    # Send sentence-start message
    if sentenceType is not SentenceType.MIDDLE:
        conn.logger.bind(tag=TAG).info(f"Sending audio message: {sentenceType}, {text}")

    # Send end message if this is the last text
    # Keep speaking state active during a call
    if not conn.calling and sentenceType == SentenceType.LAST:
        await send_tts_message(conn, "stop", None)
        if conn.close_after_chat:
            await conn.close()


async def _wait_for_audio_completion(conn: "ConnectionHandler"):
    """
    Wait for audio queue to empty and prebuffered packets to finish playing

    Args:
        conn: Connection object
    """
    if hasattr(conn, "audio_rate_controller") and conn.audio_rate_controller:
        rate_controller = conn.audio_rate_controller
        send_delay_ms = conn.config.get("tts_audio_send_delay", 0)
        conn.logger.bind(tag=TAG).debug(
            f"Waiting for audio send completion; queue still contains {len(rate_controller.queue)} packets"
        )
        await rate_controller.queue_empty_event.wait()

        if send_delay_ms > 0:
            # Custom pacing: wait for final frame to finish on client
            playback_time = 2 * rate_controller.interval_ms / 1000.0
        else:
            # Default pacing: first N frames sent directly; wait for playback
            playback_time = (PRE_BUFFER_COUNT + 2) * rate_controller.interval_ms / 1000.0
        await asyncio.sleep(playback_time)

        conn.logger.bind(tag=TAG).debug("Audio send complete")


async def _send_to_mqtt_gateway(
    conn: "ConnectionHandler", opus_packet, timestamp, sequence
):
    """
    Send Opus packets with 16-byte headers to mqtt_gateway; also cache audio for AEC
    Args:
        conn: Connection object
        opus_packet: Opus packet
        timestamp: Timestamp
        sequence: Sequence number
    """
    # If server-side AEC is enabled, cache PCM for later processing
    if conn.client_aec and timestamp > 0:
        if not hasattr(conn, "aec_audio_cache"):
            conn.aec_audio_cache = {}
            conn.aec_audio_cache_time = {}
            conn._send_opus_decoder = opuslib_next.Decoder(16000, 1)
        # Decode Opus to PCM and cache
        pcm_data = conn._send_opus_decoder.decode(bytes(opus_packet), 960)
        conn.aec_audio_cache[timestamp] = bytes(pcm_data)
        conn.aec_audio_cache_time[timestamp] = time.time()

    # Add a 16-byte header to Opus packet
    header = bytearray(16)
    header[0] = 1  # type
    header[2:4] = len(opus_packet).to_bytes(2, "big")  # payload length
    header[4:8] = sequence.to_bytes(4, "big")  # sequence
    header[8:12] = timestamp.to_bytes(4, "big")  # Timestamp
    header[12:16] = len(opus_packet).to_bytes(4, "big")  # Opus length

    # Send complete packet including header
    complete_packet = bytes(header) + opus_packet
    await conn.websocket.send(complete_packet)


async def sendAudio(
    conn: "ConnectionHandler", audios, frame_duration=AUDIO_FRAME_DURATION
):
    """
    Send audio packets with precise rate control via AudioRateController

    Args:
        conn: Connection object
        audios: Single Opus packet (bytes) or list of packets
        frame_duration: Frame duration (ms), default AUDIO_FRAME_DURATION
    """
    if audios is None or len(audios) == 0:
        return

    send_delay_ms = conn.config.get("tts_audio_send_delay", 0)
    is_single_packet = isinstance(audios, bytes)

    # Initialize or obtain RateController
    rate_controller, flow_control = _get_or_create_rate_controller(
        conn, frame_duration, is_single_packet, send_delay_ms
    )

    # Normalize into a list
    audio_list = [audios] if is_single_packet else audios

    # Send audio packets
    await _send_audio_with_rate_control(
        conn, audio_list, rate_controller, flow_control, send_delay_ms
    )


def _get_or_create_rate_controller(
    conn: "ConnectionHandler", frame_duration, is_single_packet, send_delay_ms=0
):
    """
    Get or create RateController and flow_control

    Args:
        conn: Connection object
        frame_duration: Frame duration
        is_single_packet: Whether single-packet mode (True: streamed TTS; False: batch)
        send_delay_ms: Custom send interval (milliseconds).

    Returns:
        (rate_controller, flow_control)
    """
    # Check whether controller needs resetting
    need_reset = False

    if not hasattr(conn, "audio_rate_controller"):
        # Create controller if missing
        need_reset = True
    else:
        rate_controller = conn.audio_rate_controller

        # Reset if background sender has stopped
        if (
            not rate_controller.pending_send_task
            or rate_controller.pending_send_task.done()
        ):
            need_reset = True
        # Reset when sentence_id changes
        elif (
            getattr(conn, "audio_flow_control", {}).get("sentence_id")
            != conn.sentence_id
        ):
            need_reset = True

    if need_reset:
        # Create or get rate_controller
        if not hasattr(conn, "audio_rate_controller"):
            conn.audio_rate_controller = AudioRateController(
                frame_duration, send_delay=send_delay_ms
            )
        else:
            conn.audio_rate_controller.reset()

        # Initialize flow_control
        conn.audio_flow_control = {
            "packet_count": 0,
            "sequence": 0,
            "sentence_id": conn.sentence_id,
        }

        # Start background sender loop
        _start_background_sender(
            conn, conn.audio_rate_controller, conn.audio_flow_control
        )

    return conn.audio_rate_controller, conn.audio_flow_control


def _start_background_sender(conn: "ConnectionHandler", rate_controller, flow_control):
    """
    Start background sender task

    Args:
        conn: Connection object
        rate_controller: Rate controller
        flow_control: Flow-control state
    """

    async def send_callback(packet):
        # Check whether to abort
        if conn.client_abort:
            raise asyncio.CancelledError("Client aborted")

        conn.last_activity_time = time.time() * 1000
        await _do_send_audio(conn, packet, flow_control)

    # Start background loop using start_sending
    rate_controller.start_sending(send_callback)


async def _send_audio_with_rate_control(
    conn: "ConnectionHandler", audio_list, rate_controller, flow_control, send_delay_ms
):
    """
    Send audio packets via rate_controller

    Args:
        conn: Connection object
        audio_list: List of audio packets
        rate_controller: Rate controller
        flow_control: Flow-control state
        send_delay_ms: Custom send interval (milliseconds).
    """
    for packet in audio_list:
        if conn.client_abort:
            return

        conn.last_activity_time = time.time() * 1000

        if send_delay_ms > 0:
            # Custom pacing: queue all packets at send_delay (prebuffer disabled)
            rate_controller.add_audio(packet)
        else:
            # Default pacing (60 ms/packet): prebuffer first N packets immediately, then queue remaining at interval_ms
            if flow_control["packet_count"] < PRE_BUFFER_COUNT:
                await _do_send_audio(conn, packet, flow_control)
            else:
                rate_controller.add_audio(packet)


async def _do_send_audio(conn: "ConnectionHandler", opus_packet, flow_control):
    """
    Perform actual audio send
    """
    packet_index = flow_control.get("packet_count", 0)
    sequence = flow_control.get("sequence", 0)

    if conn.conn_from_mqtt_gateway:
        # Calculate timestamp based on playback position
        start_time = time.time()
        timestamp = int(start_time * 1000) % (2**32)
        await _send_to_mqtt_gateway(conn, opus_packet, timestamp, sequence)
    else:
        # Send Opus packet directly
        await conn.websocket.send(opus_packet)

    # Update flow-control state
    flow_control["packet_count"] = packet_index + 1
    flow_control["sequence"] = sequence + 1


async def send_tts_message(conn: "ConnectionHandler", state, text=None):
    """Send TTS status message"""
    if text is None and state == "sentence_start":
        return
    message = {"type": "tts", "state": state, "session_id": conn.session_id}
    if text is not None:
        message["text"] = textUtils.check_emoji(text)

    # TTS playback ended
    if state == "stop":
        # Save current sentence_id to identify the active turn later
        current_sentence_id = conn.sentence_id
        # Play notification sound
        tts_notify = conn.config.get("enable_stop_tts_notify", False)
        if tts_notify:
            stop_tts_notify_voice = conn.config.get(
                "stop_tts_notify_voice", "config/assets/tts_notify.mp3"
            )
            audios = await audio_to_data(stop_tts_notify_voice, is_opus=True)
            await sendAudio(conn, audios)
        # Wait for all audio packets to finish sending
        await _wait_for_audio_completion(conn)

        # Check whether this is the current turn
        if current_sentence_id != conn.sentence_id:
            return

        # Stop audio send loop only when rate controller is initialized
        if hasattr(conn, "audio_rate_controller") and conn.audio_rate_controller:
            conn.audio_rate_controller.stop_sending()
        conn.clearSpeakStatus()

    # Send message to client
    await conn.websocket.send(json.dumps(message))


async def send_stt_message(conn: "ConnectionHandler", text):
    """Send STT status message"""
    end_prompt_str = conn.config.get("end_prompt", {}).get("prompt")
    if end_prompt_str and end_prompt_str == text:
        await send_tts_message(conn, "start")
        return

    # Parse JSON to extract the user's actual speech
    display_text = text
    try:
        # Try parsing JSON
        if text.strip().startswith("{") and text.strip().endswith("}"):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                # If JSON includes speaker metadata, show only content
                display_text = parsed_data["content"]
                # Save speaker metadata on connection
                if "speaker" in parsed_data:
                    conn.current_speaker = parsed_data["speaker"]
    except (json.JSONDecodeError, TypeError):
        # If not JSON, use original text
        display_text = text
    stt_text = textUtils.get_string_no_punctuation_or_emoji(display_text)
    await conn.websocket.send(
        json.dumps({"type": "stt", "text": stt_text, "session_id": conn.session_id})
    )
    await send_tts_message(conn, "start")
    # After sending start, client enters speaking state; synchronize server state
    conn.client_is_speaking = True


async def send_display_message(conn: "ConnectionHandler", text):
    """Send display-only message"""
    message = {
        "type": "stt",
        "text": text,
        "session_id": conn.session_id
    }
    await conn.websocket.send(json.dumps(message))
