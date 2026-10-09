import time
import json
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.util import audio_to_data
from core.handle.abortHandle import handleAbortMessage
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.sendAudioHandle import send_stt_message, SentenceType

TAG = __name__


async def handleAudioMessage(conn: "ConnectionHandler", pcm_frame):
    # Whether the current audio segment contains speech
    have_voice = conn.vad.is_vad(conn, pcm_frame)
    # Briefly ignore VAD if device was just awakened
    if hasattr(conn, "just_woken_up") and conn.just_woken_up:
        have_voice = False
        # Restore VAD after a short delay
        if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
            conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
        return
    # Server-side AEC requires real-time interruptions
    if conn.client_aec and have_voice:
        if conn.client_is_speaking and conn.client_listen_mode != "manual":
            await handleAbortMessage(conn)
    # Detect extended device inactivity for goodbye
    await no_voice_close_connect(conn, have_voice)
    # Receive audio
    await conn.asr.receive_audio(conn, pcm_frame, have_voice)


async def resume_vad_detection(conn: "ConnectionHandler"):
    # Resume VAD detection after two seconds
    await asyncio.sleep(2)
    conn.just_woken_up = False


async def startToChat(conn: "ConnectionHandler", text):
    # Check if input is JSON containing speaker data
    speaker_name = None
    actual_text = text

    try:
        # Try parsing JSON input
        if text.strip().startswith("{") and text.strip().endswith("}"):
            data = json.loads(text)
            if "speaker" in data and "content" in data:
                speaker_name = data["speaker"]
                actual_content = data["content"]
                conn.logger.bind(tag=TAG).info(f"Parsed speaker data: {speaker_name}")

                # Keep {"speaker":...} JSON only for a speaker's first appearance so the model addresses them naturally once;
                # use plain text on later turns to avoid repeated name greetings
                if speaker_name not in conn.introduced_speakers:
                    conn.introduced_speakers.add(speaker_name)
                    actual_text = text
                else:
                    actual_text = actual_content
    except (json.JSONDecodeError, KeyError):
        # If parsing fails, keep original text
        pass

    # Store speaker information on connection
    if speaker_name:
        conn.current_speaker = speaker_name
    else:
        conn.current_speaker = None

    if conn.need_bind:
        await check_bind_device(conn)
        return

    # If daily output exceeds the configured limit
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return

    # Do not interrupt ongoing playback in manual mode
    if conn.client_is_speaking and conn.client_listen_mode != "manual":
        await handleAbortMessage(conn)

    # Analyze intent first using actual text content
    intent_handled = await handle_user_intent(conn, actual_text)

    if intent_handled:
        # If intent is handled, skip regular chat
        return

    # Otherwise, continue normal chat with actual text
    await send_stt_message(conn, actual_text)

    # Prepare to start a new session
    conn.client_abort = False

    conn.executor.submit(conn.chat, actual_text)


async def no_voice_close_connect(conn: "ConnectionHandler", have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # Check timeout only if timestamp is initialized
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info("Ending conversation without a goodbye prompt")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "End this conversation warmly and reluctantly, beginning with the words 'Time flies'."
            await startToChat(conn, prompt)


async def max_out_size(conn: "ConnectionHandler"):
    # Play message when maximum output limit is reached
    conn.client_abort = False
    text = "Sorry, I have to go for now. Let's talk again at the same time tomorrow. See you then. Bye!"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets = await audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn: "ConnectionHandler"):
    if conn.bind_code:
        # Ensure bind_code contains six digits
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(f"Invalid binding code format: {conn.bind_code}")
            text = "Invalid binding code format. Please check your configuration."
            await send_stt_message(conn, text)
            return

        text = f"Please open the dashboard and enter {conn.bind_code} to pair the device."
        await send_stt_message(conn, text)

        # Play notification sound
        music_path = "config/assets/bind_code.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # Play digits one at a time
        for i in range(6):  # Play only six digits
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets = await audio_to_data(num_path)
                conn.tts.tts_audio_queue.put((SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Failed to play digit audio: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        # Play unbound-device prompt
        conn.client_abort = False
        text = f"No firmware version information was found for this device. Configure the OTA URL correctly and rebuild the firmware."
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
