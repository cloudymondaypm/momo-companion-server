import os
import base64
import functools
import threading
from typing import Optional, Dict

import httpx

TAG = __name__


class DeviceNotFoundException(Exception):
    pass


class DeviceBindException(Exception):
    def __init__(self, bind_code):
        self.bind_code = bind_code
        super().__init__(f"Device binding error, binding code: {bind_code}")


class ManageApiClient:
    _instance = None
    _instance_lock = threading.Lock()  # Protect access to _instance and _closed
    _async_clients = {}  # Keep a separate HTTP client per event loop
    _secret = None
    _closed = False  # Set true after safe_close(); prevent new connections

    def __new__(cls, config):
        """Singleton pattern for a unique shared instance with configurable settings"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._init_client(config)
            return cls._instance

    @classmethod
    def _init_client(cls, config):
        """Initialize configuration (create client lazily)"""
        cls.config = config.get("manager-api")

        if not cls.config:
            raise Exception("Invalid manager-api configuration")

        if not cls.config.get("url") or not cls.config.get("secret"):
            raise Exception("Invalid manager-api URL or secret")

        if "你" in cls.config.get("secret", "") or cls.config.get("secret", "").lower().startswith(("your-", "your ")):
            raise Exception("Configure manager-api.secret first")

        cls._secret = cls.config.get("secret")
        cls.max_retries = cls.config.get("max_retries", 6)  # Maximum retry attempts
        cls.retry_delay = cls.config.get("retry_delay", 10)  # Initial retry delay in seconds
        # Create AsyncClient lazily on first use
        cls._async_clients = {}
        cls._closed = False

    @classmethod
    async def _ensure_async_client(cls):
        """Ensure an async client exists for each event loop"""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)

            # Check close state and create pool atomically to avoid safe_close() races
            # A request must not recreate a client after the pool is cleared.
            with cls._instance_lock:
                if cls._closed:
                    raise Exception("ManageApiClient is closed; cannot create another HTTP client")

                if loop_id not in cls._async_clients:
                    # Server may close connections before httpx detects them
                    limits = httpx.Limits(
                        max_keepalive_connections=0,  # Disable keepalive; create a new connection per request
                    )
                    cls._async_clients[loop_id] = httpx.AsyncClient(
                        base_url=cls.config.get("url"),
                        headers={
                            "User-Agent": f"PythonClient/2.0 (PID:{os.getpid()})",
                            "Accept": "application/json",
                            "Authorization": "Bearer " + cls._secret,
                        },
                        timeout=cls.config.get("timeout", 30),
                        limits=limits,  # Connection limits
                        trust_env=False,
                    )
                return cls._async_clients[loop_id]
        except RuntimeError:
            # Create a temporary event loop if none is running
            raise Exception("This must be called from an asynchronous context")

    @classmethod
    async def _async_request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """Send one asynchronous HTTP request and handle its response"""
        # Ensure client is initialized
        client = await cls._ensure_async_client()
        endpoint = endpoint.lstrip("/")
        response = None
        try:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()

            result = response.json()

            # Handle application errors returned by API
            if result.get("code") == 10041:
                raise DeviceNotFoundException(result.get("msg"))
            elif result.get("code") == 10042:
                raise DeviceBindException(result.get("msg"))
            elif result.get("code") != 0:
                raise Exception(f"API returned an error: {result.get('msg', 'Unknown error')}")

            # Return successful data
            return result.get("data") if result.get("code") == 0 else None
        finally:
            # Always close the response, including on exceptions
            if response is not None:
                await response.aclose()

    @classmethod
    def _should_retry(cls, exception: Exception) -> bool:
        """Decide whether an exception is retryable"""
        # Network connection errors
        if isinstance(
            exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
        ):
            return True

        # HTTP status code errors
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code in [408, 429, 500, 502, 503, 504]

        return False

    @classmethod
    async def _execute_async_request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """Async request executor with retries"""
        import asyncio

        retry_count = 0

        while retry_count <= cls.max_retries:
            try:
                # Execute asynchronous request
                return await cls._async_request(method, endpoint, **kwargs)
            except Exception as e:
                # Decide whether to retry
                if retry_count < cls.max_retries and cls._should_retry(e):
                    retry_count += 1
                    print(
                        f"{method} {endpoint} Async request failed; retrying in {cls.retry_delay:.1f} seconds (attempt {retry_count} retry)"
                    )
                    await asyncio.sleep(cls.retry_delay)
                    continue
                else:
                    # Propagate the error without retrying
                    raise

    @classmethod
    def _get_instance(cls):
        """Get singleton instance reference in a thread-safe way

        Callers should use the returned local reference, not reread it after checking.
        ManageApiClient._instance：即使随后 safe_close() 将 _instance
        is set to None, the local reference still points to the original object, preventing races after checking.
        before use in the TOCTOU window.
        """
        with cls._instance_lock:
            return cls._instance

    @classmethod
    def safe_close(cls):
        """Safely close all asynchronous connection pools"""
        import asyncio

        with cls._instance_lock:
            cls._closed = True
            clients = list(cls._async_clients.values())
            cls._async_clients.clear()
            cls._instance = None

        for client in clients:
            try:
                asyncio.run(client.aclose())
            except Exception:
                pass


def api_guard(error_msg: str = None, raise_when_closed: bool = False):
    """Decorator: access singleton, handle missing instance and errors consistently

    - Use _get_instance() once to obtain a local reference and inject it as the
      first argument, preventing a TOCTOU race with safe_close().
    - If missing/closed, raise_when_closed=True raises a clear error;
      otherwise return None for background services.
    - When error_msg is set, log request errors and return None;
      otherwise let the caller handle the exception.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            instance = ManageApiClient._get_instance()
            if instance is None:
                if raise_when_closed:
                    raise Exception("ManageApiClient is not initialized or is closed")
                return None
            if error_msg is None:
                return await func(instance, *args, **kwargs)
            try:
                return await func(instance, *args, **kwargs)
            except Exception as e:
                print(f"{error_msg}: {e}")
                return None

        return wrapper

    return decorator


@api_guard(raise_when_closed=True)
async def get_server_config(instance) -> Optional[Dict]:
    """获取服务器基础配置"""
    return await instance._execute_async_request("POST", "/config/server-base")


@api_guard(raise_when_closed=True)
async def get_agent_models(
    instance, mac_address: str, client_id: str, selected_module: Dict
) -> Optional[Dict]:
    """获取代理模型配置"""
    return await instance._execute_async_request(
        "POST",
        "/config/agent-models",
        json={
            "macAddress": mac_address,
            "clientId": client_id,
            "selectedModule": selected_module,
        },
    )


@api_guard("获取替换词失败")
async def get_correct_words(instance, mac_address: str) -> Optional[Dict]:
    """获取智能体替换词"""
    return await instance._execute_async_request(
        "POST", "/config/correct-words",
        json={"macAddress": mac_address}
    )


@api_guard("生成并保存聊天记录总结失败")
async def generate_and_save_chat_summary(instance, session_id: str) -> Optional[Dict]:
    """生成并保存聊天记录总结（守护线程中调用，服务已关闭时静默返回 None）"""
    return await instance._execute_async_request(
        "POST",
        f"/agent/chat-summary/{session_id}/save",
    )


@api_guard("生成并保存聊天标题失败")
async def generate_and_save_chat_title(instance, session_id: str) -> Optional[Dict]:
    """生成并保存聊天标题（守护线程中调用，服务已关闭时静默返回 None）"""
    return await instance._execute_async_request(
        "POST",
        f"/agent/chat-title/{session_id}/generate",
    )


@api_guard("TTS上报失败")
async def report(
    instance, mac_address: str, session_id: str, chat_type: int, content: str, audio, report_time
) -> Optional[Dict]:
    """异步聊天记录上报"""
    if not content:
        return None
    return await instance._execute_async_request(
        "POST",
        f"/agent/chat-history/report",
        json={
            "macAddress": mac_address,
            "sessionId": session_id,
            "chatType": chat_type,
            "content": content,
            "reportTime": report_time,
            "audioBase64": (
                base64.b64encode(audio).decode("utf-8") if audio else None
            ),
        },
    )


@api_guard("通讯录查找失败")
async def lookup_address_book(instance, caller_mac: str, nickname: str) -> Optional[Dict]:
    """根据昵称查找目标设备"""
    return await instance._execute_async_request(
        "GET",
        f"/device/address-book/lookup?callerMac={caller_mac}&nickname={nickname}",
    )


def init_service(config):
    ManageApiClient(config)


def manage_api_http_safe_close():
    ManageApiClient.safe_close()
