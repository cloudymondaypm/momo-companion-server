# MQTT + UDP Gateway Integration

Momo Companion can use the [xiaozhi-mqtt-gateway](https://github.com/78/xiaozhi-mqtt-gateway) ecosystem for MQTT+UDP device connections. This guide covers gateway deployment, full management-console settings, and standalone server settings.

## Prerequisites

Prepare the MQTT gateway's WebSocket connection URL by adding `?from=mqtt_gateway` to your AI server endpoint:

```text
# Server running from source on the same host
ws://127.0.0.1:8000/xiaozhi/v1/?from=mqtt_gateway

# Gateway running on a different host or in Docker
ws://192.168.1.25:8000/xiaozhi/v1/?from=mqtt_gateway
```

**Required ports:** The original gateway uses MQTT TCP `1883`, UDP `8884`, and management API TCP `8007`. Allow these ports between the gateway, server and authorized devices. Do not expose the management port unnecessarily.

## Part 1. Deploy the MQTT gateway

### 1. Clone the gateway

```bash
git clone https://github.com/xinnan-tech/xiaozhi-mqtt-gateway.git
cd xiaozhi-mqtt-gateway
npm install
npm install -g pm2
```

### 2. Set the WebSocket upstream

```bash
cp config/mqtt.json.example config/mqtt.json
```

Edit `config/mqtt.json` to point `chat_servers` to the Momo Companion AI server:

```json
{
  "production": {
    "chat_servers": [
      "ws://192.168.1.25:8000/xiaozhi/v1/?from=mqtt_gateway"
    ]
  },
  "debug": false,
  "max_mqtt_payload_size": 8192,
  "mcp_client": {
    "capabilities": {},
    "client_info": {
      "name": "xiaozhi-mqtt-client",
      "version": "1.0.0"
    },
    "max_tools_count": 128
  }
}
```

### 3. Configure environment variables

Create `.env` in the gateway project root:

```dotenv
PUBLIC_IP=192.168.1.25
MQTT_PORT=1883
UDP_PORT=8884
API_PORT=8007
MQTT_SIGNATURE_KEY=YOUR_STRONG_MQTT_SIGNING_SECRET
SERVER_SECRET=YOUR_SERVER_AUTH_SECRET
```

- `PUBLIC_IP` can be a reachable host IP or domain according to your deployment.
- `MQTT_SIGNATURE_KEY` must be a strong secret (the original guide recommends at least eight characters containing uppercase and lowercase letters). Do not use `test` or `123456`.
- `SERVER_SECRET` must match the corresponding configured secret if server authentication is enabled:
  - **Full-module:** Management console `server.secret`.
  - **Standalone:** AI server `server.auth_key`.

### 4. Start the gateway

```bash
pm2 start ecosystem.config.js
pm2 logs xz-mqtt
```

The logs should indicate listeners for MQTT TCP port 1883 and UDP port 8884.

To restart:

```bash
pm2 restart xz-mqtt
```

## Part 2. Full management console configuration

The original integration guide expects management console version `0.7.7` or newer.

Under **Parameter Management**, set the following values:

| Parameter | Value / example |
| --- | --- |
| `server.mqtt_gateway` | MQTT host and port: `192.168.1.25:1883` |
| `server.mqtt_signature_key` | Same secret as `MQTT_SIGNATURE_KEY` |
| `server.udp_gateway` | UDP host and port: `192.168.1.25:8884` |
| `server.mqtt_manager_api` | Gateway management API: `192.168.1.25:8007` |

Make sure these hostnames/IPs are reachable from the ESP32 device. The gateway configuration is delivered to the device through the **OTA endpoint**.

### Test OTA response

Replace the example URL with your full-module OTA endpoint:

```bash
curl 'http://localhost:8002/xiaozhi/ota/' \
  -H 'Content-Type: application/json' \
  -H 'Client-Id: 7b94d69a-9808-4c59-9c9b-704333b38aff' \
  -H 'Device-Id: 11:22:33:44:55:66' \
  --data-raw '{
    "application": {"version": "1.0.1", "elf_sha256": "1"},
    "board": {"mac": "11:22:33:44:55:66"}
  }'
```

A correctly configured response should contain an `mqtt` object with values such as `endpoint`, `client_id`, `username`, `password`, `publish_topic`, and `subscribe_topic` alongside the normal OTA and WebSocket information.

Once the device has received the OTA response, reconnect or reboot it, then verify the gateway logs:

```bash
pm2 logs xz-mqtt
```

## Part 3. Standalone server configuration

Edit `data/.config.yaml`. Under the existing `server` section, set:

```yaml
server:
  mqtt_gateway: 192.168.1.25:1883
  mqtt_signature_key: YOUR_STRONG_MQTT_SIGNING_SECRET
  udp_gateway: 192.168.1.25:8884
```

The signing key must match the gateway's `.env`. Merge this into your existing `server` mapping rather than defining the mapping twice.

### Test standalone OTA response

Use the standalone OTA port (`8003` by default):

```bash
curl 'http://localhost:8003/xiaozhi/ota/' \
  -H 'Content-Type: application/json' \
  -H 'Device-Id: 11:22:33:44:55:66' \
  --data-raw '{
    "application": {"version": "1.0.1", "elf_sha256": "1"},
    "board": {"mac": "11:22:33:44:55:66"}
  }'
```

Verify the response includes an `mqtt` configuration. If not, check the signing key, gateway ports, and that you are using the correct OTA endpoint.

Restart or wake the device, then inspect:

```bash
pm2 logs xz-mqtt
```

**Note:** The server/gateway must be running and the device must successfully receive its OTA response for MQTT settings to take effect.
