from __future__ import annotations

import asyncio
import json
import re
import urllib.error
import urllib.request
import uuid
from typing import Any

from ..base import MemoryProviderBase, logger

TAG = __name__


class MemoryProvider(MemoryProviderBase):
    """Honcho-backed semantic memory for Xiaozhi conversations."""

    def __init__(self, config: dict[str, Any], summary_memory=None):
        super().__init__(config)
        self.base_url = str(config.get("base_url", "")).rstrip("/")
        self.workspace_id = str(config.get("workspace_id", "xiaozhi"))
        self.api_key = str(config.get("api_key", ""))
        self.peer_prefix = str(config.get("peer_prefix", "xiaozhi"))
        self.search_limit = max(1, min(int(config.get("search_limit", 8)), 20))
        self.max_context_chars = max(
            500, min(int(config.get("max_context_chars", 4000)), 12000)
        )
        self.timeout = max(2, min(int(config.get("timeout", 10)), 60))
        self.enabled = bool(self.base_url)
        if self.enabled:
            logger.bind(tag=TAG).info(
                f"Honcho memory configured: base_url={self.base_url}, "
                f"workspace={self.workspace_id}"
            )
        else:
            logger.bind(tag=TAG).error("Honcho memory base_url is missing")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(self, method: str, path: str, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers=self._headers(),
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace")
            raise RuntimeError(f"Honcho HTTP {exc.code}: {detail}") from exc

    def _safe_id(self, value: Any, fallback: str) -> str:
        value = str(value or fallback)
        value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
        return value[:180] or fallback

    def _peer_id(self) -> str:
        return self._safe_id(
            f"{self.peer_prefix}-{getattr(self, 'role_id', None) or 'default'}",
            f"{self.peer_prefix}-default",
        )

    def _session_id(self, session_id: str | None) -> str:
        return self._safe_id(
            f"{self.peer_prefix}-{session_id or uuid.uuid4().hex}",
            f"{self.peer_prefix}-{uuid.uuid4().hex}",
        )

    def _ensure_peer_and_session(self, peer_id: str, session_id: str) -> None:
        workspace = self.workspace_id
        assistant_id = self._safe_id(f"{self.peer_prefix}-assistant", "xiaozhi-assistant")
        for candidate in (peer_id, assistant_id):
            try:
                self._request(
                    "POST", f"/v3/workspaces/{workspace}/peers", {"id": candidate}
                )
            except Exception as exc:
                if "409" not in str(exc):
                    raise
        try:
            self._request(
                "POST", f"/v3/workspaces/{workspace}/sessions", {"id": session_id}
            )
        except Exception as exc:
            if "409" not in str(exc):
                raise
        try:
            self._request(
                "POST",
                f"/v3/workspaces/{workspace}/sessions/{session_id}/peers",
                {
                    peer_id: {"observe_me": True, "observe_others": False},
                    assistant_id: {"observe_me": False, "observe_others": True},
                },
            )
        except Exception as exc:
            if "409" not in str(exc):
                raise

    @staticmethod
    def _content(value: Any) -> str:
        content = str(value or "")
        try:
            if content.strip().startswith("{") and content.strip().endswith("}"):
                data = json.loads(content)
                content = str(data.get("content", content))
        except (json.JSONDecodeError, TypeError):
            pass
        return content.strip()

    def _save_sync(self, msgs, session_id: str | None) -> None:
        peer_id = self._peer_id()
        honcho_session = self._session_id(session_id)
        self._ensure_peer_and_session(peer_id, honcho_session)
        workspace = self.workspace_id
        messages = []
        assistant_id = self._safe_id(
            f"{self.peer_prefix}-assistant", "xiaozhi-assistant"
        )
        for message in msgs:
            role = getattr(message, "role", "")
            if role not in {"user", "assistant"}:
                continue
            content = self._content(getattr(message, "content", ""))
            if not content:
                continue
            sender = peer_id if role == "user" else assistant_id
            messages.append({"content": content, "peer_id": sender})
        if messages:
            self._request(
                "POST",
                f"/v3/workspaces/{workspace}/sessions/{honcho_session}/messages",
                {"messages": messages[-100:]},
            )

    async def save_memory(self, msgs, session_id=None):
        if not self.enabled or len(msgs) < 2:
            return None
        try:
            await asyncio.to_thread(self._save_sync, msgs, session_id)
            logger.bind(tag=TAG).info(
                f"Saved Xiaozhi conversation to Honcho for peer {self._peer_id()}"
            )
        except Exception as exc:
            logger.bind(tag=TAG).error(f"Honcho memory save failed: {exc}")
        return None

    def _query_sync(self, query: str) -> str:
        workspace = self.workspace_id
        peer_id = self._peer_id()
        try:
            result = self._request(
                "GET",
                f"/v3/workspaces/{workspace}/peers/{peer_id}/context",
            )
            context_parts = []
            for key in ("representation", "peer_card", "summary", "context", "content"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    context_parts.append(value.strip())
                elif isinstance(value, (list, dict)) and value:
                    context_parts.append(json.dumps(value, ensure_ascii=False))
            if context_parts:
                return "\n".join(context_parts)[: self.max_context_chars]
            return ""
        except Exception as exc:
            logger.bind(tag=TAG).debug(f"Honcho context unavailable: {exc}")
        result = self._request(
            "POST",
            f"/v3/workspaces/{workspace}/peers/{peer_id}/search",
            {"query": self._content(query), "limit": self.search_limit},
        )
        rows = result if isinstance(result, list) else result.get("data", result.get("results", []))
        memories = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            content = row.get("content") or row.get("text") or row.get("message")
            if isinstance(content, dict):
                content = content.get("content") or content.get("text")
            if content:
                memories.append(f"- {str(content).strip()}")
        return "\n".join(memories)[: self.max_context_chars]

    async def query_memory(self, query: str) -> str:
        if not self.enabled or not getattr(self, "role_id", None):
            return ""
        try:
            return await asyncio.to_thread(self._query_sync, query)
        except Exception as exc:
            if "404" not in str(exc):
                logger.bind(tag=TAG).error(f"Honcho memory query failed: {exc}")
            return ""
