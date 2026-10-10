# Opt-in Android hybrid voice

Legacy Xiaozhi/ESP32 devices keep their current hello, listen, abort, binary Opus
frames, TTS notifications, MQTT gateway framing, memory and tool routing.

A hybrid Android connection adds `Voice-Mode: hybrid-v1` to the upgrade request,
plus existing `Device-Id`, `Client-Id`, and an OTA-issued `Authorization: Bearer`
token. Unlike legacy LAN connections, hybrid always verifies the device-bound
token, even if legacy authentication is disabled or a whitelist bypass exists.
Credentials are no longer included in connection header logs.

The client requests `features.hybrid_voice = 1` in hello; the server advertises
the same after its runtime is ready. Audio parameters remain unchanged.

Send `{"type":"conversation","session_id":"...","text":"...","response_mode":"device"}`
for recognized/typed text, or choose `server` to receive normal server TTS.
Maximum input: 8000 characters. The existing `startToChat` path still controls
intent, tools, dialogue, memory and reporting. `listen/start` can also include
`response_mode`, allowing server STT plus local TTS on the older watch.

Local output intercepts TTS text DTOs before synthesis and emits the assembled
reply as a normal `tts/sentence_start` with `output: device` and `turn_id`, followed
by stop. It preserves text reporting and output accounting without generating
speech audio. Replies longer than 24000 characters and explicit tool audio files
use the original server audio path. ASR/TTS modules stay available for fallback;
this saves per-turn speech work, not all model residency or idle threads.

If local TTS fails, send `{"type":"tts_request","session_id":"...","turn_id":"..."}`.
The server synthesizes the latest cached reply once, without repeating the LLM,
memory write or tools. Stale, aborted and duplicate playback requests are rejected.
Replay does not duplicate text reporting/output accounting. Android suppresses
duplicate displayed subtitles on this replay.

Tests: `python -m unittest discover -s tests/hybrid -v`. These are independent of
optional ML/audio dependencies and run in CI. Live provider and physical-device
verification is still needed. Momo's separate paired-device service is in the
`momo-ai-server` repository; its tokens are not Xiaozhi HMAC bearer tokens.
