import hmac
import base64
import hashlib
import time


class AuthenticationError(Exception):
    """Authentication exception"""

    pass


class AuthManager:
    """
    Unified authentication manager
    Generate and verify client_id, device_id and token (HMAC-SHA256)
    Tokens carry only signature and timestamp; client_id/device_id are sent at connection time
    In MQTT client_id: client_id, username: device_id, password: token
    In WebSocket，header:{Device-ID: device_id, Client-ID: client_id, Authorization: Bearer token, ......}
    """

    def __init__(self, secret_key: str, expire_seconds: int = 60 * 60 * 24 * 30):
        if not expire_seconds or expire_seconds < 0:
            self.expire_seconds = 60 * 60 * 24 * 30
        else:
            self.expire_seconds = expire_seconds
        self.secret_key = secret_key

    def _sign(self, content: str) -> str:
        """Sign with HMAC-SHA256 and encode in Base64"""
        sig = hmac.new(
            self.secret_key.encode("utf-8"), content.encode("utf-8"), hashlib.sha256
        ).digest()
        return base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")

    def generate_token(self, client_id: str, username: str) -> str:
        """
        Generate token
        Args:
            client_id: Device connection ID
            username: Device username (usually deviceId)
        Returns:
            str: Token string
        """
        ts = int(time.time())
        content = f"{client_id}|{username}|{ts}"
        signature = self._sign(content)
        # Token contains only signature and timestamp
        token = f"{signature}.{ts}"
        return token

    def verify_token(self, token: str, client_id: str, username: str) -> bool:
        """
        Validate token
        Args:
            token: Token received from client
            client_id: client_id used by connection
            username: Username used by connection
        """
        try:
            sig_part, ts_str = token.split(".")
            ts = int(ts_str)
            if int(time.time()) - ts > self.expire_seconds:
                return False  # Expired

            expected_sig = self._sign(f"{client_id}|{username}|{ts}")
            if not hmac.compare_digest(sig_part, expected_sig):
                return False

            return True
        except Exception:
            return False
