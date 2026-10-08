# Weather Plugin Guide

## Overview

The `get_weather` plugin lets Momo Companion answer spoken weather queries. It uses the QWeather (HeWeather) API for current conditions and seven-day forecasts.

## Obtain an API key

1. Open the [QWeather Console](https://console.qweather.com/) and create an account.
2. Verify your email address and sign in.
3. In [Project Management](https://console.qweather.com/project?lang=zh), select **Create Project** and enter a name such as **Momo Companion**.
4. Save the project, then select **Create Credential**.
5. Provide a credential name, select **API Key** authentication, and save.
6. Copy the generated `API Key`.
7. In [QWeather Settings](https://console.qweather.com/setting?lang=zh), locate your assigned **API Host** and copy it.

You will need both `API Key` and `API Host`.

## Configure the plugin

### Option 1: Management console (recommended)

1. Sign in to the management console.
2. Open **Agent Configuration** and select the agent.
3. Choose **Edit Functions** and find **Weather Query**.
4. Enable the weather plugin.
5. Enter the **Weather Plugin API Key** and **Developer API Host** obtained above.
6. Save the function settings, then save the agent configuration.

### Option 2: Standalone xiaozhi-server

Edit `data/.config.yaml`, replacing the placeholders with your QWeather credentials and a default city:

```yaml
plugins:
  get_weather:
    api_key: YOUR_QWEATHER_API_KEY
    api_host: YOUR_QWEATHER_API_HOST
    default_location: "Guangzhou"
```

Restart the server after changing the configuration.
