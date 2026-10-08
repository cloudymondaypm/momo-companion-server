# Automatic Firmware OTA Updates in Standalone Deployments

This guide explains automatic firmware OTA updates for a **standalone xiaozhi-server deployment**. If you use the full management console deployment, use its OTA management features instead.

## How it works

The standalone server can check a device's model and currently installed firmware version, find a matching newer firmware image, and make it available for download.

## Prerequisites

- A running standalone `xiaozhi-server`.
- The device successfully connects to the server.

## Step 1. Prepare the firmware

### Create the firmware directory

Firmware files belong in `data/bin/`:

```bash
mkdir -p data/bin
```

### Follow the naming convention

```text
{device-model}_{firmware-version}.bin
```

- **Device model** must match the identifier reported by the device (for example, `lichuang-dev` or `bread-compact-wifi`).
- **Firmware version** must begin with a digit and may contain numbers, letters, periods, underscores, and hyphens (for example, `1.6.6` or `2.0.0`).
- The extension must be `.bin`.

Examples:

```text
bread-compact-wifi_1.6.6.bin
lichuang-dev_2.0.0.bin
```

**Important:** Use the OTA update image `xiaozhi.bin`, **not** the full flash image `merged-binary.bin`. Uploading a merged image as an OTA update can render the device unusable.

```bash
cp xiaozhi.bin data/bin/bread-compact-wifi_1.6.6.bin
```

## Step 2. Configure public access (only for internet-facing deployments)

If the server is exposed through a public IP or domain, set `server.vision_explain`. The standalone OTA implementation uses its hostname and port when generating firmware download URLs.

Skip this section if devices access the server directly over your local network and the generated URLs already work.

Edit `data/.config.yaml`:

```yaml
server:
  vision_explain: http://your-hostname:8003/mcp/vision/explain
```

For a local deployment, an example is:

```yaml
server:
  vision_explain: http://192.168.1.100:8003/mcp/vision/explain
```

For a public domain, use the address your device can actually reach. If a reverse proxy handles HTTPS, configure the externally reachable URL rather than an internal Docker hostname, `localhost`, or `127.0.0.1`.

## Troubleshooting

### The device does not receive an update

- Confirm the filename matches `{device-model}_{firmware-version}.bin`.
- Confirm it is located in `data/bin/`.
- Confirm the device model matches the filename.
- Make sure the firmware version is newer than the device's installed version.
- Review the server logs for OTA request handling.

### The device cannot access the download URL

- Confirm that `server.vision_explain` points to the correct publicly reachable hostname/IP and port (default HTTP port: `8003`).
- Check firewall rules, Docker port publishing, and reverse-proxy configuration.
- Do not use a Docker-only address or loopback hostname for an external device.

### How can I confirm the device firmware version?

The server's OTA request logs should include the version reported by the device, for example:

```text
[ota_handler] - Device AA:BB:CC:DD:EE:FF firmware is up to date: 1.6.6
```

The exact log message may vary by server version.

### My new firmware file is not detected

The firmware list may be cached for approximately 30 seconds by default. Trigger a new OTA check after the cache expires, restart the server, or adjust `firmware_cache_ttl` if supported by your configuration.
