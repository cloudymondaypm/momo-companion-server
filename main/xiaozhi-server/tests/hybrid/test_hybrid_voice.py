"""Run independently of optional audio/ML libraries: python -m unittest discover -s tests/hybrid."""
import asyncio
import json
import queue
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.auth import AuthManager
from core.hybrid_voice import HybridTextQueue, handle_hybrid_message, verify_hybrid_auth
from core.providers.tts.dto.dto import ContentType, SentenceType, TTSMessageDTO


def connection():
    conn = types.SimpleNamespace(
        hybrid_negotiated=True, hybrid_ready=True, hybrid_busy=False,
        hybrid_output="device", client_abort=False, client_is_speaking=False,
        session_id="session", sentence_id="turn", hybrid_reply=None,
        websocket=types.SimpleNamespace(send=AsyncMock()), clearSpeakStatus=lambda: None,
    )
    conn.tts = types.SimpleNamespace(tts_text_queue=HybridTextQueue(conn))
    return conn


class AuthTests(unittest.TestCase):
    def test_hybrid_bearer_is_bound_to_both_ids(self):
        auth = AuthManager("test-secret")
        token = auth.generate_token("client", "device")
        headers = {"device-id": "device", "client-id": "client", "authorization": "Bearer " + token}
        self.assertTrue(verify_hybrid_auth(auth, headers))
        for altered in ({"device-id": "other"}, {"client-id": "other"}, {"authorization": ""}):
            self.assertFalse(verify_hybrid_auth(auth, {**headers, **altered}))


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_text_reuses_existing_conversation_router(self):
        conn = connection()
        backend = types.ModuleType("core.handle.receiveAudioHandle")
        backend.startToChat = AsyncMock()
        reporting = types.ModuleType("core.handle.reportHandle")
        reporting.enqueue_asr_report = lambda *args: None
        with patch.dict(sys.modules, {backend.__name__: backend, reporting.__name__: reporting}):
            self.assertTrue(await handle_hybrid_message(conn, {
                "type": "conversation", "session_id": "session", "text": "Kumusta?", "response_mode": "device",
            }))
            backend.startToChat.assert_awaited_once_with(conn, "Kumusta?")
            self.assertTrue(conn.hybrid_busy)

    async def test_negotiation_session_limits_and_busy_are_enforced(self):
        for changes, request, expected in (
            ({"hybrid_negotiated": False}, {}, "hybrid_not_negotiated"),
            ({"hybrid_ready": False}, {}, "not_ready"),
            ({}, {"session_id": "other"}, "invalid_session"),
            ({}, {"text": "x" * 8001}, "invalid_request"),
            ({}, {"text": " "}, "invalid_request"),
            ({"hybrid_busy": True}, {}, "busy"),
        ):
            conn = connection()
            for key, value in changes.items():
                setattr(conn, key, value)
            await handle_hybrid_message(conn, {"type": "conversation", "session_id": "session", "text": "hello", **request})
            self.assertEqual(json.loads(conn.websocket.send.call_args.args[0])["code"], expected)

    async def test_local_output_never_enters_synthesis_queue(self):
        conn = connection()
        conn.loop = asyncio.get_running_loop()
        for stage, text in ((SentenceType.FIRST, None), (SentenceType.MIDDLE, "Kumusta "),
                            (SentenceType.MIDDLE, "Momo!"), (SentenceType.LAST, None)):
            conn.tts.tts_text_queue.put(TTSMessageDTO("turn", stage, ContentType.TEXT, text))
        await asyncio.sleep(0.01)
        self.assertTrue(conn.tts.tts_text_queue.empty())
        self.assertEqual(conn.hybrid_reply, ("turn", "Kumusta Momo!"))
        sent = [json.loads(call.args[0]) for call in conn.websocket.send.call_args_list]
        self.assertEqual([value["state"] for value in sent], ["sentence_start", "stop"])
        self.assertFalse(conn.hybrid_busy)

    async def test_legacy_and_server_output_keep_original_dtos(self):
        conn = connection()
        conn.hybrid_negotiated = False
        item = TTSMessageDTO("turn", SentenceType.MIDDLE, ContentType.TEXT, "hello")
        conn.tts.tts_text_queue.put(item)
        self.assertIs(conn.tts.tts_text_queue.get_nowait(), item)
        conn.hybrid_negotiated = True
        conn.hybrid_output = "server"
        conn.tts.tts_text_queue.put(item)
        self.assertIs(conn.tts.tts_text_queue.get_nowait(), item)
        self.assertFalse(await handle_hybrid_message(conn, {"type": "listen"}))

    async def test_tts_fallback_replays_cached_reply_only_once(self):
        conn = connection()
        conn.hybrid_reply = ("turn", "Cached answer")
        backend = types.ModuleType("core.handle.receiveAudioHandle")
        backend.startToChat = AsyncMock()
        request = {"type": "tts_request", "session_id": "session", "turn_id": "turn"}
        with patch.dict(sys.modules, {backend.__name__: backend}):
            await handle_hybrid_message(conn, request)
            self.assertEqual(conn.tts.tts_text_queue.qsize(), 3)
            self.assertEqual(conn.tts.tts_text_queue.get_nowait().sentence_type, SentenceType.FIRST)
            self.assertEqual(conn.tts.tts_text_queue.get_nowait().content_detail, "Cached answer")
            backend.startToChat.assert_not_called()
            await handle_hybrid_message(conn, request)
            self.assertEqual(json.loads(conn.websocket.send.call_args.args[0])["code"], "busy")

    async def test_tool_media_and_long_replies_fall_back_to_audio_without_losing_text(self):
        for item in (TTSMessageDTO("turn", SentenceType.MIDDLE, ContentType.FILE, content_file="music.wav"),
                     TTSMessageDTO("turn", SentenceType.MIDDLE, ContentType.TEXT, "x" * 24001)):
            conn = connection()
            conn.tts.tts_text_queue.put(TTSMessageDTO("turn", SentenceType.MIDDLE, ContentType.TEXT, "Before "))
            conn.tts.tts_text_queue.put(item)
            self.assertEqual(conn.hybrid_output, "server")
            self.assertEqual(conn.tts.tts_text_queue.get_nowait().sentence_type, SentenceType.FIRST)
            self.assertEqual(conn.tts.tts_text_queue.get_nowait().content_detail, "Before ")
            self.assertIs(conn.tts.tts_text_queue.get_nowait(), item)

    async def test_aborted_and_stale_local_output_is_discarded(self):
        conn = connection()
        await conn.tts.tts_text_queue.finish("old", "stale")
        conn.client_abort = True
        await conn.tts.tts_text_queue.finish("turn", "aborted")
        conn.websocket.send.assert_not_called()
        conn.hybrid_reply = ("old", "stale")
        await handle_hybrid_message(conn, {"type": "tts_request", "session_id": "session", "turn_id": "old"})
        self.assertEqual(json.loads(conn.websocket.send.call_args.args[0])["code"], "stale_turn")


if __name__ == "__main__":
    unittest.main()
