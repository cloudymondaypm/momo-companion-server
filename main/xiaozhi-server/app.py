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


async def wait_for_exit() -> None:
    """
    Block until Ctrl-C or SIGTERM is received.
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
        # Windows: await a future that never completes,
        # allowing KeyboardInterrupt to propagate to asyncio.run and prevent shutdown blocking from remaining threads
        try:
            await asyncio.Future()
        except KeyboardInterrupt:  # Ctrl‑C
            pass


async def monitor_stdin():
    """Monitor standard input and consume Enter presses"""
    while True:
        await ainput()  # Await input asynchronously and consume Enter


async def main():
    check_ffmpeg_installed()
    config = await load_config()

    # auth_key priority: config server.auth_key > manager-api.secret > generated key
    # auth_key supports JWT for vision endpoint, OTA tokens, and WebSocket authentication
    # Get auth_key from config file
    auth_key = config["server"].get("auth_key", "")
    
    # Validate auth_key; fall back to manager-api.secret if invalid
    if not auth_key or len(auth_key) == 0 or "你" in auth_key:
        auth_key = config.get("manager-api", {}).get("secret", "")
        # Validate secret; generate a random key if invalid
        if not auth_key or len(auth_key) == 0 or "你" in auth_key:
            auth_key = str(uuid.uuid4().hex)
    
    config["server"]["auth_key"] = auth_key

    # Add stdin monitor task
    stdin_task = asyncio.create_task(monitor_stdin())

    # Start global garbage collector (clean up every five minutes)
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
        "Vision endpoint:\thttp://{}:{}/mcp/vision/explain",
        get_local_ip(),
        port,
    )
    mcp_endpoint = config.get("mcp_endpoint", None)
    if mcp_endpoint is not None and "你" not in mcp_endpoint:
        # Validate MCP endpoint format
        if validate_mcp_endpoint(mcp_endpoint):
            logger.bind(tag=TAG).info("MCP endpoint:\t{}", mcp_endpoint)
            # Convert MCP endpoint to callable URL
            mcp_endpoint = mcp_endpoint.replace("/mcp/", "/call/")
            config["mcp_endpoint"] = mcp_endpoint
        else:
            logger.bind(tag=TAG).error("MCP endpoint format is invalid")
            config["mcp_endpoint"] = "你的接入点 websocket地址"

    # Load WebSocket configuration with safe defaults
    websocket_port = 8000
    server_config = config.get("server", {})
    if isinstance(server_config, dict):
        websocket_port = int(server_config.get("port", 8000))

    logger.bind(tag=TAG).info(
        "WebSocket address:\tws://{}:{}/xiaozhi/v1/",
        get_local_ip(),
        websocket_port,
    )

    logger.bind(tag=TAG).info(
        "=======The address above uses WebSocket; do not open it in a browser======="
    )
    logger.bind(tag=TAG).info(
        "To test WebSocket, start the digital-human module and use its browser interface"
    )
    logger.bind(tag=TAG).info(
        "=============================================================\n"
    )

    try:
        await wait_for_exit()  # Block until shutdown signal
    except asyncio.CancelledError:
        print("Task cancelled; cleaning up resources...")
    finally:
        # Stop global garbage collector
        await gc_manager.stop()

        # Cancel all tasks (critical shutdown fix)
        stdin_task.cancel()
        ws_task.cancel()
        if ota_task:
            ota_task.cancel()

        # Wait for tasks to terminate (with a timeout)
        await asyncio.wait(
            [stdin_task, ws_task, ota_task] if ota_task else [stdin_task, ws_task],
            timeout=3.0,
            return_when=asyncio.ALL_COMPLETED,
        )
        print("Server stopped. Exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted manually. Exiting.")
