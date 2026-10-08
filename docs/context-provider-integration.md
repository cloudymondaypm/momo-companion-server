# Context Providers: Inject Live Data into the Agent Prompt

## Overview

A **context provider** supplies external information to Momo Companion's system prompt at the moment the device wakes up. The server fetches one or more HTTP endpoints and inserts their responses so the model has an up-to-date snapshot of the world.

Context providers are different from **memory** (which retains information from earlier conversations) and **MCP/function calling** (which retrieves information or performs actions on demand). A context provider injects a snapshot automatically. To retrieve changing data later in the same conversation, also use an MCP tool.

Examples include health-sensor readings, server load, outstanding work items, financial data, or any API that returns text-friendly JSON.

## How it works

1. Configure one or more HTTP API URLs.
2. When the prompt template contains `{{ dynamic_context }}`, the server calls all configured APIs.
3. It formats the returned data as Markdown and replaces `{{ dynamic_context }}` in the system prompt.

## API contract

- **Method:** `GET`.
- **Request header:** The system adds `device-id` automatically.
- **Response:** JSON object containing `code` and `data` fields.

### Example 1. Return a dictionary

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "Living room temperature": "26°C",
    "Living room humidity": "45%",
    "Front door": "Closed"
  }
}
```

Injected prompt:

```text
<context>
- **Living room temperature:** 26°C
- **Living room humidity:** 45%
- **Front door:** Closed
</context>
```

### Example 2. Return a list

```json
{
  "code": 0,
  "data": [
    "You have ten pending tasks",
    "Vehicle speed is currently 100 km/h"
  ]
}
```

Injected prompt:

```text
<context>
- You have ten pending tasks
- Vehicle speed is currently 100 km/h
</context>
```

## Configure context providers

### Full management console

1. Sign in and open **Agent Configuration**.
2. Locate **Context Providers** and choose **Edit Sources**.
3. Click **Add** and enter the API URL.
4. If authentication is required, add request headers such as `Authorization`.
5. Save the provider settings.

### Standalone server

Edit `main/xiaozhi-server/data/.config.yaml`:

```yaml
context_providers:
  - url: "http://api.example.com/data"
    headers:
      Authorization: "Bearer your-token"
  - url: "http://another-api.com/data"
```

## Enable the prompt variable

The default prompt template may already contain the `{{ dynamic_context }}` placeholder. If you use a customized template, ensure the placeholder is present:

```text
<context>
[IMPORTANT: This information is supplied in real time. Use it without additional tool calls.]
- **Device ID:** {{device_id}}
- **Current time:** {{current_time}}
{{ dynamic_context }}
</context>
```

If you do not need context providers, leave the provider list empty or remove `{{ dynamic_context }}` from the prompt template.

## Appendix. Local mock API server

Save the following as `mock_api_server.py` and run it to simulate the context-provider protocol on port `8081`:

```python
import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

PORT = 8081

class MockRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        print(f"Request: {path}; query: {query}")
        data = {}
        status = 200

        if path == "/health":
            device_id = self.headers.get("device-id", "unknown_device")
            data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "Test device ID": device_id,
                    "Heart rate": "80 bpm",
                    "Blood pressure": "120/80 mmHg",
                    "Status": "Good",
                },
            }
        elif path == "/news/list":
            data = {
                "code": 0,
                "msg": "success",
                "data": [
                    "Technology: AI assistants are changing daily life",
                    "Local weather: bring an umbrella tomorrow",
                ],
            }
        elif path == "/weather/simple":
            data = {
                "code": 0,
                "msg": "success",
                "data": "Partly cloudy, 20–25°C, good air quality.",
            }
        elif path == "/device/info":
            device_id = self.headers.get("device-id", "unknown_device")
            data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "Lookup method": "Header parameter",
                    "Device ID": device_id,
                    "Battery": "85%",
                    "Firmware": "v2.0.1",
                },
            }
        else:
            status = 404
            data = {"error": "Endpoint not found"}

        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MockRequestHandler) as server:
    print(f"Mock API server at http://localhost:{PORT}")
    print(f"GET /health, /news/list, /weather/simple, /device/info")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
```

Test `http://localhost:8081/health`, then add it to your context-provider list.
