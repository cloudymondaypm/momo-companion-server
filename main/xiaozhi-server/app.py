import sys
import uuid
import signal
import asyncio
from aioconsole import ainput
from config.settings import load_config
from config.logger import setup_logging
from core.utils.util import get_local_ip, validate_mcp_endpoint
from core.http_server import SimpleHttpServer
from core.websocket_server import WebSocketServer
from core.utils.util import check_ffmpeg_installed
from core.utils.gc_manager import get_gc_manager

TAG = __name__
logger = setup_logging()


def _missing_config(value):
    """True when a setting is unset or still contains a documentation placeholder."""
    if not value:
        return True
    setting = str(value).strip().lower()
    return "你" in setting or setting.startswith(("your-", "your ", "your_"))


async def wait_for_exit() -> None:
    """
    Block until Ctrl-C or SIGTERM.
    - Unix: Use add_signal_handler
    - Windows: Rely on KeyboardInterrupt
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    if sys.platform != "win32":  # Unix / macOS
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
    else:
        # On Windows, await a never-completing future
        # so KeyboardInterrupt reaches asyncio.run and exits without blocking on lingering threads.
        try:
            await asyncio.Future()
        except KeyboardInterrupt:  # Ctrl‑C
            pass


async def monitor_stdin():
    """Monitor stdin and consume Enter key presses"""
    while True:
        await ainput()  # Asynchronously wait for input


async def main():
    check_ffmpeg_installed()
    config = await load_config()

    # auth_key priority: server.auth_key > manager-api.secret > generated key
    # auth_key signs JWT for vision analysis, OTA tokens, and WebSocket authentication
    # Read auth_key from configuration
    auth_key = config["server"].get("auth_key", "")
    
    # If auth_key is missing, try manager-api.secret
    if _missing_config(auth_key):
        auth_key = config.get("manager-api", {}).get("secret", "")
        # Generate a random secret if manager-api.secret is missing
        if _missing_config(auth_key):
            auth_key = str(uuid.uuid4().hex)
    
    config["server"]["auth_key"] = auth_key

    # Start stdin monitor task
    stdin_task = asyncio.create_task(monitor_stdin())

    # Start global GC manager (every five minutes)
    gc_manager = get_gc_manager(interval_seconds=300)
    await gc_manager.start()

    # Start WebSocket server
    ws_server = WebSocketServer(config)
    ws_task = asyncio.create_task(ws_server.start())
    # Start simple HTTP server
    ota_server = SimpleHttpServer(config)
    ota_task = asyncio.create_task(ota_server.start())

    read_config_from_api = config.get("read_config_from_api", False)
    port = int(config["server"].get("http_port", 8003))
    if not read_config_from_api:
        logger.bind(tag=TAG).info(
            "OTA endpoint:\t\thttp://{}:{}/xiaozhi/ota/",
            get_local_ip(),
            port,
        )
    logger.bind(tag=TAG).info(
        "Vision analysis endpoint:\thttp://{}:{}/mcp/vision/explain",
        get_local_ip(),
        port,
    )
    mcp_endpoint = config.get("mcp_endpoint", None)
    if not _missing_config(mcp_endpoint):
        # Validate MCP endpoint URL
        if validate_mcp_endpoint(mcp_endpoint):
            logger.bind(tag=TAG).info("MCP endpoint:\t{}", mcp_endpoint)
            # Convert MCP endpoint to tool call endpoint
            mcp_endpoint = mcp_endpoint.replace("/mcp/", "/call/")
            config["mcp_endpoint"] = mcp_endpoint
        else:
            logger.bind(tag=TAG).error("Invalid MCP endpoint URL")
            config["mcp_endpoint"] = "your-mcp-endpoint-url"

    # Read WebSocket config using safe defaults
    websocket_port = 8000
    server_config = config.get("server", {})
    if isinstance(server_config, dict):
        websocket_port = int(server_config.get("port", 8000))

    logger.bind(tag=TAG).info(
        "WebSocket URL:\tws://{}:{}/xiaozhi/v1/",
        get_local_ip(),
        websocket_port,
    )

    logger.bind(tag=TAG).info(
        "=======The URL above is a WebSocket endpoint; do not open it in a browser======="
    )
    logger.bind(tag=TAG).info(
        "To test WebSockets, start digital-human and use its browser interface."
    )
    logger.bind(tag=TAG).info(
        "=============================================================\n"
    )

    try:
        await wait_for_exit()  # Block until exit signal
    except asyncio.CancelledError:
        print("Task canceled; cleaning up resources...")
    finally:
        # Stop global GC manager
        await gc_manager.stop()

        # Cancel all tasks (important cleanup)
        stdin_task.cancel()
        ws_task.cancel()
        if ota_task:
            ota_task.cancel()

        # Wait for task termination with a timeout
        await asyncio.wait(
            [stdin_task, ws_task, ota_task] if ota_task else [stdin_task, ws_task],
            timeout=3.0,
            return_when=asyncio.ALL_COMPLETED,
        )
        print("Server shut down. Exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted manually. Exiting.")
