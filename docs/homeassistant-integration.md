# Home Assistant Integration for Momo Companion

Connect your ESP32 voice assistant to [Home Assistant](https://www.home-assistant.io/) so it can read device states and control smart-home devices. Three integration methods are described below.

## Prerequisites

- A working Home Assistant installation with devices/entities already configured.
- A reachable Home Assistant URL, such as `http://192.168.4.7:8123` or `http://homeassistant.local:8123`.
- An appropriate Home Assistant access token.
- For function-calling options, a language model that supports tools/function calling.

### Find your Home Assistant address

In Home Assistant, open **Settings → System → Network**. Under the local network/Home Assistant URL section, view and copy the current URL.

![Network address in Home Assistant](images/image-ha-integration-01.png)

### Generate a long-lived access token

In Home Assistant, open your user profile and locate **Security → Long-Lived Access Tokens**. Create and securely save a token. The full token may be shown only once; do not publish it in documentation or source control.

## Method 1. Use the built-in community Home Assistant functions

This approach uses Momo Companion's existing functions for reading Home Assistant entity states and changing them. If new devices are added to Home Assistant, the original integration may require an AI server restart to refresh entity information.

### 1. Find the entities to control

Open **Settings → Devices & Services → Entities**. Find the relevant lights or switches and confirm that they work in Home Assistant.

Record each entity's **Entity ID** and build a device list using the following format:

```text
location,device_name,entity_id;
```

Example:

```text
Living room,Toy light,switch.cuco_cn_460494544_cp1_on_p_2_1;
Bedroom,Desk lamp,switch.iot_cn_831898993_socn1_on_p_2_1;
```

These are sample identifiers only; use your own real Home Assistant entity IDs.

### 2. Enable the functions for an agent

Sign in to Momo Companion's management console:

1. Open **Agent Management → Agent Configuration**.
2. Set Intent Recognition to an LLM-backed function-calling mode.
3. Choose **Edit Functions**.
4. Enable **Home Assistant Device State Query** and **Home Assistant Device State Update**.
5. Enter your Home Assistant URL, access token, and device list under the function's parameters.
6. Save the function configuration and then save the agent.

![Management console setup](images/image-ha-integration-06.png)

### 3. Test from the ESP32

Wake the assistant and say something like **"Turn on the desk lamp."** Check Home Assistant history and server logs if the request fails.

## Method 2. Use Home Assistant's conversation agent as the LLM

This method routes conversation handling to Home Assistant's configured conversation/LLM agent. **Limitation:** The original integration does not simultaneously expose all of the server's built-in function-call plugins.

### 1. Configure a conversation agent

Set up the Home Assistant voice/conversation agent that you want Momo Companion to use.

### 2. Find its Agent ID

1. Open Home Assistant **Developer Tools → Actions**.
2. Choose `conversation.process` (Conversation: Process).
3. Enable the **Agent** field and select your configured conversation agent.
4. Switch the action to **YAML mode**.
5. Copy the agent ID from the YAML.

![Conversation process action](images/image-ha-integration-02.png)
![Select conversation agent](images/image-ha-integration-03.png)
![YAML mode](images/image-ha-integration-04.png)
![Copy agent ID](images/image-ha-integration-05.png)

### 3. Configure Momo Companion

In `main/xiaozhi-server/data/.config.yaml`, configure your Home Assistant provider with its URL, token and agent ID, then select:

```yaml
selected_module:
  LLM: HomeAssistant
  Intent: nointent
```

Keep the existing `LLM.HomeAssistant` provider settings and update only the necessary values. Restart the AI server.

## Method 3. Use Home Assistant MCP Server (recommended for tools)

This method retains Momo Companion's own LLM and function-calling capabilities while exposing Home Assistant tools through the official [Model Context Protocol Server integration](https://www.home-assistant.io/integrations/mcp_server/).

### 1. Enable the integration in Home Assistant

Open [Settings → Devices & Services](https://my.home-assistant.io/redirect/integrations), select [Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=mcp_server), search for **Model Context Protocol Server**, and complete its setup.

### 2. Add MCP server connection settings

Create `main/xiaozhi-server/data/.mcp_server_settings.json` if it does not exist. You can copy the default `mcp_server_settings.json` from the server root first.

Add the Home Assistant entry under the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "Home Assistant": {
      "command": "mcp-proxy",
      "args": [
        "http://192.168.1.101:8123/mcp_server/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "YOUR_HOME_ASSISTANT_TOKEN"
      }
    }
  }
}
```

The URL above is from the original integration guide. Confirm the correct MCP endpoint/path and transport mode for your Home Assistant release, and make sure the `mcp-proxy` executable is installed where the Python server runs.

**JSON tip:** Remove any trailing comma after the last `mcpServers` entry; trailing commas make standard JSON invalid.

### 3. Select a function-calling LLM

Choose any supported LLM with reliable function calling; do not use the `HomeAssistant` LLM adapter for this method. Select tool-based intent recognition:

```yaml
selected_module:
  Intent: function_call
```

Configure your chosen `selected_module.LLM` and its API settings as usual, then restart the AI server.

### 4. Verify tool access

Ask Momo Companion to read or change a device state. Check the MCP connection logs and Home Assistant permissions if the tool is missing or unauthorized.
