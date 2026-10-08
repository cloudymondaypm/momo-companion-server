# Connect MCP Tools to Momo Companion

This guide uses the upstream [MCP calculator example](https://github.com/78/mcp-calculator) to demonstrate registering a custom tool at your MCP endpoint.

**Prerequisite:** Complete [Deploy and Configure an MCP Endpoint](mcp-endpoint-enable.md) first.

## 1. Find your agent's MCP endpoint

### Full management console

Open **Agent Management → Agent Configuration**, select your agent, and choose **Edit Functions** beside Intent Recognition. Locate the **MCP Endpoint URL** at the bottom of the functions dialog and copy it.

### Standalone xiaozhi-server

Find the MCP WebSocket URL from the server startup logs or your `data/.config.yaml`, for example:

```text
ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

Keep this URL private, as its token authorizes tool registration.

## 2. Download and install the calculator example

Download or clone [mcp-calculator](https://github.com/78/mcp-calculator) and enter its directory:

```bash
cd mcp-calculator
conda create -n mcp-calculator python=3.10 -y
conda activate mcp-calculator
pip install -r requirements.txt
```

If the `mcp-calculator` Conda environment already exists, reuse it or remove it separately only when you really want a clean install.

## 3. Start the calculator service

Set `MCP_ENDPOINT` to the URL copied earlier:

```bash
export MCP_ENDPOINT='ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc'
python mcp_pipe.py calculator.py
```

On Windows PowerShell, use `$env:MCP_ENDPOINT = 'ws://...'` instead of `export`.

## 4. Verify tool registration

### Management console

Return to the agent's MCP feature settings and refresh the MCP connection status. The calculator tool should appear in the registered function list.

### Standalone server

Connect a device and inspect logs for MCP initialization, connection success, the registered server name (`Calculator`), and a function list containing `calculator`.

Example:

```text
MCP endpoint connection successful
MCP endpoint initialization successful
MCP endpoint server: name=Calculator, version=1.9.4
MCP tools available: 1
Supported functions: ['get_time', 'get_lunar', 'play_music', 'get_weather', 'handle_exit_intent', 'calculator']
```

If `calculator` appears, your device can invoke it through tool/function calling when the selected language model supports that feature.
