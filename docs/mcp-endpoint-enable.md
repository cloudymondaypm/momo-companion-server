# Deploy and Configure an MCP Endpoint

This guide covers three steps: deploying the standalone MCP endpoint service, connecting it to the full management console, and configuring a standalone xiaozhi-server deployment.

## 1. Deploy the MCP endpoint service

### Download the project

Open the upstream [mcp-endpoint-server repository](https://github.com/xinnan-tech/mcp-endpoint-server). Clone it, or use GitHub's **Code → Download ZIP** and extract the folder as `mcp-endpoint-server`.

### Start the service

Docker is the recommended deployment method. See the [developer setup guide](https://github.com/xinnan-tech/mcp-endpoint-server/blob/main/README_dev.md) to run it from source instead.

```bash
cd mcp-endpoint-server

# Optional cleanup of previously installed containers
docker compose -f docker-compose.yml down
docker stop mcp-endpoint-server
docker rm mcp-endpoint-server
docker rmi ghcr.nju.edu.cn/xinnan-tech/mcp-endpoint-server:latest

# Start
docker compose -f docker-compose.yml up -d
docker logs -f mcp-endpoint-server
```

The endpoint service logs should publish two different addresses, for example:

```text
Management console health endpoint: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
Standalone WebSocket endpoint:      ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
```

**Important:** `172.22.0.2` may be a Docker-internal address that devices and the management console cannot access. Replace it with the host's reachable LAN or public address, such as `192.168.1.25`:

```text
Management console health endpoint: http://192.168.1.25:8004/mcp_endpoint/health?key=abc
Standalone WebSocket endpoint:      ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

Open the **health** URL in a browser to confirm a response similar to:

```json
{"result":{"status":"success","connections":{"tool_connections":0,"robot_connections":0,"total_connections":0}},"error":null,"id":null,"jsonrpc":"2.0"}
```

Keep both endpoint URLs and their tokens confidential.

## 2. Full management console deployment

1. Sign in to the console and open **Parameter Dictionary → System Feature Configuration**.
2. Enable **MCP Endpoint** and save.
3. Go to an agent's **Agent Configuration → Edit Functions** to find the MCP feature.
4. As administrator, open **Parameter Dictionary → Parameter Management**.
5. Locate `server.mcp_endpoint` (usually initially empty or `null`).
6. Set its value to the **management console health endpoint URL** from Step 1 and save.

If validation fails, confirm that the console can reach port 8004, your firewall allows the request, and you did not use Docker's internal IP.

## 3. Standalone server deployment

Edit `data/.config.yaml` and set the `mcp_endpoint` key to the **WebSocket endpoint URL** from Step 1:

```yaml
server:
  websocket: ws://192.168.1.25:8000/xiaozhi/v1/
  http_port: 8003
log:
  log_level: INFO

mcp_endpoint: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

Keep any other server settings already present and do not introduce a second `server` YAML mapping. The HTTP port example may differ for your deployment.

After restarting the server, check the logs for the MCP endpoint URL:

```text
MCP endpoint: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

If it appears and the endpoint connects successfully, the configuration is working. See [Connect MCP Tools](mcp-endpoint-integration.md) for the next step.
