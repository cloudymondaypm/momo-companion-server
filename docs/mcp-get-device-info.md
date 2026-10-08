# Access Device Information in MCP Tools

This guide shows how to make the current device ID available to MCP tools through the system prompt.

## Step 1. Copy the base prompt template

Copy `agent-base-prompt.txt` from the `xiaozhi-server` directory into its `data` subdirectory, naming the copy `.agent-base-prompt.txt`.

## Step 2. Add the device ID to the context

Edit `data/.agent-base-prompt.txt` and include a `{{device_id}}` variable within the `<context>` block:

```text
<context>
[IMPORTANT: The information below is already supplied in real time. Use it without calling a tool.]
- **Device ID:** {{device_id}}
- **Current time:** {{current_time}}
- **Today's date:** {{today_date}} ({{today_weekday}})
- **Lunar date:** {{lunar_date}}
- **User's city:** {{local_address}}
- **Next seven days of local weather:** {{weather_info}}
</context>
```

Preserve any additional context variables your deployment uses.

## Step 3. Point the server to the customized prompt

In `data/.config.yaml`, replace:

```yaml
prompt_template: agent-base-prompt.txt
```

with:

```yaml
prompt_template: data/.agent-base-prompt.txt
```

## Step 4. Restart the server

Restart `xiaozhi-server` to load the updated prompt.

## Step 5. Define the MCP argument

Add an argument to your MCP tool named `device_id`, with type `string` and description **Device ID**.

## Step 6. Test

Wake Momo Companion, ask it to invoke the MCP function, and confirm that the `device_id` parameter is populated correctly.
