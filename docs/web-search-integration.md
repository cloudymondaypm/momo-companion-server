# Web Search Plugin Guide

## Overview

The `web_search` function searches the internet during a conversation and returns relevant results. Three providers are supported: **Metaso**, **Tavily**, and **Serply**. Configure one based on the content and API availability you need.

## Obtain a provider API key

- **Metaso:** Go to [Metaso API Keys](https://metaso.cn/search-api/api-keys), create an account, and choose **Create New Key**. Keys generally have an `mk-` prefix. Metaso is oriented toward sources in China.
- **Tavily:** Sign in to the [Tavily console](https://app.tavily.com/home), create an API key, and copy it. Keys generally have a `tvly-` prefix.
- **Serply:** Register at [Serply](https://serply.io), create an API key, and refer to the [Serply API documentation](https://serply.io/docs).

Provider quotas and prices may change. Check each provider's current free-tier limits before choosing.

## Configure the plugin

### Option 1: Management console (recommended)

1. Sign in and open **Agent Configuration**.
2. Select the agent and choose **Edit Functions**.
3. Enable **Web Search** in the plugin list.
4. Set the provider to `metaso`, `tavily`, or `serply`, and enter its API key.
5. Save the function configuration, then save the agent.

### Option 2: Standalone server

Edit `data/.config.yaml` and add the provider settings:

```yaml
plugins:
  web_search:
    provider: "metaso"
    api_key: YOUR_SEARCH_API_KEY
```

Optionally customize the tool description and maximum result count:

```yaml
plugins:
  web_search:
    provider: "metaso"
    description: "Search the web when the user requests current or online information."
    max_results: 5
    api_key: YOUR_SEARCH_API_KEY
```

Also ensure `web_search` is enabled in the functions list. **Merge this setting into your existing `plugins` section** rather than adding a second YAML key:

```yaml
plugins:
  functions:
    - web_search
```

Restart the server for changes to take effect.
