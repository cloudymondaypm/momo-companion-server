# Build ESP32 Firmware for Your Own Server

This guide explains how to compile Xiaozhi ESP32 firmware and point it to a self-hosted Momo Companion backend.

## 1. Prepare the OTA endpoint

Both the standalone and full-module server deployments provide an OTA endpoint.

### Standalone server

Open your local endpoint in a browser, for example:

```text
http://192.168.1.25:8003/xiaozhi/ota/
```

The response should indicate that the OTA endpoint is healthy and show a WebSocket URL such as `ws://192.168.1.25:8000/xiaozhi/v1/`.

To test the WebSocket connection interactively, start the `digital-human` module and open its test page. If connection fails, review `server.websocket` in `data/.config.yaml`, restart the server, and retry.

### Full-module server

Open the management API OTA endpoint, for example:

```text
http://192.168.1.25:8002/xiaozhi/ota/
```

A healthy endpoint reports the number of WebSocket servers. If configuration is missing, sign in as superadmin to the management console, open **Parameter Management**, and set `server.websocket` to an address the ESP32 device can reach:

```text
ws://192.168.1.25:8000/xiaozhi/v1/
```

Refresh the OTA endpoint to verify the change.

## 2. Install ESP-IDF

Set up the ESP-IDF toolchain appropriate to your firmware version. The upstream project includes a [Windows ESP-IDF 5.3.2 installation and build guide](https://icnynnzcwou8.feishu.cn/wiki/JEYDwTTALi5s2zkGlFGcDiRknXf).

## 3. Download the ESP32 firmware source

Clone or download the upstream [xiaozhi-esp32 repository](https://github.com/78/xiaozhi-esp32). Open:

```text
xiaozhi-esp32/main/Kconfig.projbuild
```

## 4. Set the OTA URL

Find `config OTA_URL` and replace its default value with your server's actual URL.

**Before:**

```kconfig
config OTA_URL
    string "Default OTA URL"
    default "https://api.tenclass.net/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```

**After (example):**

```kconfig
config OTA_URL
    string "Default OTA URL"
    default "http://192.168.1.25:8002/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```

Use port `8003` instead for a standalone OTA endpoint if that is how your deployment is configured. For devices outside your LAN, use a public device-reachable URL and secure transport where required.

## 5. Configure the firmware target

From the firmware source root:

```bash
cd xiaozhi-esp32

# Example for an ESP32-S3; replace with your actual chip target
idf.py set-target esp32s3
idf.py menuconfig
```

In the configuration menu, open **Xiaozhi Assistant** and set `BOARD_TYPE` to match the exact board model. Save and exit.

## 6. Build firmware

```bash
idf.py build
```

## 7. Package the firmware

```bash
cd scripts
python release.py
```

The release script is expected to generate `build/merged-binary.bin`. This **merged image is used for initial full-device flashing**, not for standalone OTA update files. If packaging reports an optional ZIP error but the merged firmware exists, inspect the generated output to determine whether packaging succeeded.

## 8. Flash the ESP32

Connect the ESP32 device to your computer. Open [ESP Launchpad](https://espressif.github.io/esp-launchpad/) in Chrome or another compatible browser. The [upstream web flashing guide](https://ccnphfhqs21z.feishu.cn/wiki/Zpz4wXBtdimBrLk25WdcXzxcnNS) describes the ESP Launchpad method.

Once flashed and connected to Wi-Fi, wake the device and check the Momo Companion server logs.

## Troubleshooting

See the [FAQ](FAQ.md) for wrong-language ASR detection, TTS failures, 4G connections, slow responses, and speech interruption behavior.
