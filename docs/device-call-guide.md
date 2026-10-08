# Device-to-Device Calling Plugin Guide

## Overview

Device calling provides bidirectional communication between two registered devices. When A calls B, the flow is:

```
Device A → Authorization → MQTT gateway → Remote wake-up of Device B → Connection → Call established
```
## Prerequisites
1. At least two devices must use ESP32-S3 hardware, which supports remote wake-up in the documented firmware.
2. Two microphones are recommended. Single-microphone devices may work, but expect degraded call quality.
3. Use [full-module deployment](Deployment_all.md) because the management console manages call permissions and connections.
4. Install an [MQTT gateway](mqtt-gateway-integration.md) build dated May 27, 2026 or newer.

The steps below assume these requirements are satisfied.

## Configuration

### Step 1. Enable the address book

1. Confirm your management console is version 0.9.4 or later.
2. Sign in to the management console
3. Open **System Feature Configuration**
4. Enable **Address Book**
5. Click **Save Configuration** to confirm

### Step 2. Configure device call permissions

1. In the top navigation menu, select **Address Book**
2. Select Device A in the agent's device list (search by MAC address or nickname)
3. In the details panel, select a nickname for Device B, such as **"Alex"**
4. Enable Device B's **call permission** checkbox
5. Click **Save**

**Bidirectional permissions:** To allow mutual calling, configure permissions for both devices:

- Allow B in A's configuration → A can call B
- Allow A in B's configuration → B can call A

### Step 3. Enable the calling tool for the agent

1. In the top navigation menu, select **Agent Management**
2. For the agent linked to the devices, click **Edit Agent**
3. In the right-hand details panel, click **Edit Functions**
4. Enable the **Device-to-device Call** tool
5. Click **Save Configuration** to confirm
6. Save the overall agent configuration and restart the device

### Step 4. Add the remote wake-up tool to firmware

1. In[xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) add an MCP remote wake-up tool for firmware versions 2.1.0–2.2.6 (May 29, 2026 builds).
2. Add a remote wake-up declaration to application.h:
    ```cpp
    void RemoteWakeup(const std::string& reason);
    ```
3. Add the implementation to application.cc:
    ```cpp
    void Application::RemoteWakeup(const std::string& reason){
        if (!protocol_) {
            return;
        }

        auto state = GetDeviceState();
        
        if (state == kDeviceStateIdle) {
            audio_service_.EncodeWakeWord();

            if (!protocol_->IsAudioChannelOpened()) {
                SetDeviceState(kDeviceStateConnecting);
                if (!protocol_->OpenAudioChannel()) {
                    audio_service_.EnableWakeWordDetection(true);
                    return;
                }
            }
            std::string wake_word = reason;
    #if CONFIG_USE_AFE_WAKE_WORD || CONFIG_USE_CUSTOM_WAKE_WORD
            // Encode and send the wake word data to the server
            while (auto packet = audio_service_.PopWakeWordPacket()) {
                protocol_->SendAudio(std::move(packet));
            }
            // Set the chat state to wake word detected
            protocol_->SendWakeWordDetected(wake_word);
            SetListeningMode(aec_mode_ == kAecOff ? kListeningModeAutoStop : kListeningModeRealtime);
    #else
            // Set flag to play popup sound after state changes to listening
            // (PlaySound here would be cleared by ResetDecoder in EnableVoiceProcessing)
            play_popup_on_listening_ = true;
            SetListeningMode(aec_mode_ == kAecOff ? kListeningModeAutoStop : kListeningModeRealtime);
    #endif
        } else if (state == kDeviceStateSpeaking) {
            AbortSpeaking(kAbortReasonWakeWordDetected);
            SetDeviceState(kDeviceStateIdle);
        } else if (state == kDeviceStateActivating) {
            SetDeviceState(kDeviceStateIdle);
        }
    }
    ```
4. Register the MCP tool in mcp_server.cc:
    ```cpp
    AddUserOnlyTool("self.remote_wakeup", "Remote wakeup function with configurable parameters",
        PropertyList({
            Property("reason", kPropertyTypeString, "Wakeup reason"),
        }),
        [this](const PropertyList& properties) -> ReturnValue {
            std::string reason = properties["reason"].value<std::string>();
            ESP_LOGI(TAG, "Wakeup reason=%s", reason.c_str());
            auto& app = Application::GetInstance();
            app.RemoteWakeup(reason);
            return true;
        });
    ```
5. Follow [Firmware Build Guide](firmware-build.md) to build and flash the device
6. Enable **AEC** in the firmware settings regardless of the number of microphones.

### Step 5. Set up the MQTT gateway

1. Deploy the gateway following [MQTT gateway integration](mqtt-gateway-integration.md)
2. If already deployed, confirm the gateway build is dated May 27, 2026 or later.

## Test a call

Configure both devices and enable the calling tool. On Device A, say "Call Alex" (or the target nickname) and check whether Device B responds.

## Troubleshooting

### Q: Why does Device B not answer?

- Check whether Device B is online in the console
- Verify Device B has the remote wake-up firmware tool
- Verify the MQTT gateway connection
- Check permissions on both devices

### Q: Why does the system report no permission to call?

- Enable permission to call B from Device A
- Ensure the configuration is saved

### Q: How do I confirm that the address book is enabled?

- The **Address Book** entry should be visible in the console's top navigation.

### Q: ASR mishears the contact nickname. How do I fix this?
- Check whether your ASR provider supports hotwords.
- For `FunASRServer`, add the contact's exact name to its hotword file and restart the container.
- For Volcengine ASR, configure the hotword table in the provider console, then set the matching hotword table name under the model's ASR configuration in Momo Companion.

