"""Opt-in text transport over the existing authenticated Xiaozhi socket.

No separate LLM, memory store or tool dispatcher. Legacy connections never enter
this module's output path. TTS fallback replays cached text, not the agent turn.
"""
import asyncio
import json
import queue
import time

from core.providers.tts.dto.dto import ContentType, SentenceType, TTSMessageDTO

MAX_TEXT = 8000
MAX_REPLY = 24000


def verify_hybrid_auth(auth, headers):
    """Hybrid clients require a device-bound bearer even on an open LAN server."""
    token = headers.get("authorization", "")
    device = headers.get("device-id", "")
    client = headers.get("client-id", "")
    return bool(device and client and token.startswith("Bearer ") and
                auth.verify_token(token[7:], client_id=client, username=device))


async def error(conn, code):
    await conn.websocket.send(json.dumps({"type": "error", "code": code}))


async def handle_hybrid_message(conn, msg):
    kind = msg.get("type")
    if kind not in ("conversation", "tts_request"):
        return False
    if not getattr(conn, "hybrid_negotiated", False):
        await error(conn, "hybrid_not_negotiated")
        return True
    if not getattr(conn, "hybrid_ready", False):
        await error(conn, "not_ready")
        return True
    if msg.get("session_id") != conn.session_id:
        await error(conn, "invalid_session")
        return True
    if kind == "tts_request":
        cached = getattr(conn, "hybrid_reply", None)
        if (not cached or msg.get("turn_id") != cached[0] or
                cached[0] != conn.sentence_id or conn.client_abort):
            await error(conn, "stale_turn")
            return True
        if conn.hybrid_busy or getattr(conn, "hybrid_replayed", False):
            await error(conn, "busy")
            return True
        conn.hybrid_replayed = True
        conn.hybrid_output = "server"
        conn.hybrid_busy = True
        conn.client_is_speaking = True
        # Bypass the local-output queue. Never call chat or the tool router.
        await conn.websocket.send(json.dumps({"type": "tts", "state": "start",
                                             "session_id": conn.session_id}))
        for stage, content in ((SentenceType.FIRST, None),
                               (SentenceType.MIDDLE, cached[1]),
                               (SentenceType.LAST, None)):
            queue.Queue.put(conn.tts.tts_text_queue, TTSMessageDTO(
                cached[0], stage, ContentType.TEXT if content else ContentType.ACTION,
                content_detail=content))
        return True
    text = msg.get("text")
    output = msg.get("response_mode", "server")
    if (not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT or
            output not in ("device", "server")):
        await error(conn, "invalid_request")
        return True
    if conn.hybrid_busy or conn.client_is_speaking:
        await error(conn, "busy")
        return True
    conn.hybrid_busy = True
    conn.hybrid_output = output
    conn.hybrid_reply = None
    conn.hybrid_replayed = False
    conn.last_activity_time = time.time() * 1000
    conn.client_listen_mode = "manual"
    conn.client_abort = False
    from core.handle.receiveAudioHandle import startToChat
    try:
        from core.handle.reportHandle import enqueue_asr_report
        enqueue_asr_report(conn, text.strip(), [])
        await startToChat(conn, text.strip())
    except Exception:
        conn.hybrid_busy = False
        await error(conn, "conversation_failed")
    return True


class HybridTextQueue(queue.Queue):
    """Intercept local-output DTOs before any TTS provider synthesizes them."""
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.turn = None
        self.parts = []
        self.size = 0

    def put(self, item, block=True, timeout=None):
        conn = self.conn
        if (not getattr(conn, "hybrid_negotiated", False) or
                getattr(conn, "hybrid_output", "server") != "device"):
            return super().put(item, block, timeout)
        if conn.client_abort or item.sentence_id != conn.sentence_id:
            return
        if self.turn != item.sentence_id:
            self.turn, self.parts, self.size = item.sentence_id, [], 0
        if (item.content_type == ContentType.FILE or
                (item.content_type == ContentType.TEXT and item.content_detail and
                 self.size + len(str(item.content_detail)) > MAX_REPLY)):
            # Tools may play media; very long replies also use the audio path.
            conn.hybrid_output = "server"
            super().put(TTSMessageDTO(item.sentence_id, SentenceType.FIRST, ContentType.ACTION))
            if self.parts:
                super().put(TTSMessageDTO(item.sentence_id, SentenceType.MIDDLE,
                                         ContentType.TEXT, "".join(self.parts)))
            self.parts = []
            return super().put(item, block, timeout)
        if item.content_type == ContentType.TEXT and item.content_detail:
            part = str(item.content_detail)
            self.parts.append(part)
            self.size += len(part)
        if item.sentence_type == SentenceType.LAST:
            reply = "".join(self.parts)
            self.parts = []
            asyncio.run_coroutine_threadsafe(self.finish(item.sentence_id, reply), conn.loop)

    async def finish(self, turn, text):
        conn = self.conn
        if conn.client_abort or turn != conn.sentence_id:
            return
        conn.hybrid_reply = (turn, text)
        await conn.websocket.send(json.dumps({"type": "tts", "state": "sentence_start",
            "text": text, "output": "device", "turn_id": turn, "session_id": conn.session_id}, ensure_ascii=False))
        await conn.websocket.send(json.dumps({"type": "tts", "state": "stop",
            "output": "device", "turn_id": turn, "session_id": conn.session_id}))
        conn.clearSpeakStatus()
        conn.hybrid_busy = False
        report = getattr(conn, "hybrid_report_reply", None)
        if report and text:
            report(text)
        if getattr(conn, "close_after_chat", False):
            await conn.close()
