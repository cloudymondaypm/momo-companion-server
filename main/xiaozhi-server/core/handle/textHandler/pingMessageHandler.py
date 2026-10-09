import json
import time
from typing import Dict, Any

from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType

TAG = __name__


class PingMessageHandler(TextMessageHandler):
    """Ping message handler used to keep the WebSocket connection alive"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.PING

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        """
        Handle PING message and send PONG
        Message format: {"type": "ping"}
        Args:
            conn: WebSocket connection object
            msg_json: PING message JSON data
        """
        # Check whether WebSocket heartbeat is enabled
        enable_websocket_ping = conn.config.get("enable_websocket_ping", False)
        if not enable_websocket_ping:
            conn.logger.debug(f"WebSocket heartbeat disabled; ignoring PING")
            return

        try:
            conn.logger.debug(f"PING received; sending PONG")
            conn.last_activity_time = time.time() * 1000
            # Build PONG response
            pong_message = {
                "type": "pong",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }

            # Send PONG response
            await conn.websocket.send(json.dumps(pong_message))

        except Exception as e:
            conn.logger.error(f"Error handling PING message: {e}")
