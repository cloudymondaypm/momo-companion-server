# Point Existing Xiaozhi Firmware to a Custom Server

## Step 1. Confirm firmware version

Flash [Xiaozhi firmware version 1.6.1 or newer](https://github.com/78/xiaozhi-esp32/releases), as provided by the upstream device project.

## Step 2. Check your OTA address

If you deployed the full management system, your server should expose an OTA endpoint. Open that endpoint in your browser, for example:

```text
https://your-domain.example/xiaozhi/ota/
```

If the response indicates that the OTA endpoint is healthy and shows a WebSocket cluster count, proceed to Step 3.

If the response says an OTA setting is missing, sign in to the **management console** as a superadmin, open **Parameter Management**, and check `server.websocket`. Enter the public WebSocket endpoint, for example:

```text
wss://your-domain.example/xiaozhi/v1/
```

Refresh the OTA endpoint. If it still reports a problem, make sure the WebSocket server is running and that the configured URL is reachable from the device.

## Step 3. Enter Wi-Fi provisioning mode

Put the device into provisioning mode. Under **Advanced Options**, enter your server's OTA URL, save the settings, and restart the device.

![OTA URL configuration](images/firmware-setting-ota.png)

## Step 4. Wake the assistant and verify logs

Wake the device and check that the server logs show a successful connection and conversation requests.

## Common questions

See [Frequently Asked Questions](FAQ.md) for fixes to:

- Speech detected as the wrong language
- Missing TTS files or TTS timeouts
- Wi-Fi connections working while 4G connections fail
- Slow responses
- Voice activity detection interrupting long pauses
- Smart home device control and extensions
