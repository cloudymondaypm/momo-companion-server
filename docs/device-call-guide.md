# Device-to-Device Calling Plugin Guide

## Overview

Device calling provides bidirectional communication between two registered devices. When A calls B, the flow is:

```
Device A → Authorization → MQTT gateway → Remote wake-up of Device B → Connection → Call established
```
## Prerequisites
1. At least two devices are required; both must use`ESP32-S3`，because only`ESP32-S3`supports remote wake-up in the documented firmware。
2. The devices should have`two microphones`。If the devices have only`one microphone`，the feature can still be tried, but call quality may be poor。
3. Use[full-module deployment](Deployment_all.md)because the`management console`is required to control permissions and communication。
4. Install and configure the`May 27, 2026`or newer[MQTT gateway](mqtt-gateway-integration.md)，If installed already, check it is from`May 27, 2026`or later。

The steps below assume these requirements are satisfied.

## Configuration

### Step 1. Enable the address book

1. Confirm the management console version is`0.9.4`or later。
2. Sign in to the management console
3. Open **System Feature Configuration**
4. Enable **Address Book**
5. Click **Save Configuration** to confirm

### Step 2. Configure device call permissions

1. In the top navigation menuClick **Address Book**
2. Select Device A in the agent's device list (search by MAC address or nickname)
3. In the details panel, select a nickname for Device B, such as **"Alex"**
4. Enable Device B's **call permission** checkbox
5. Click **Save**

**Bidirectional permissions:** To allow mutual calling, configure permissions for both devices:

- Allow B in A's configuration → A can call B
- Allow A in B's configuration → B can call A

### Step 3. Enable the calling tool for the agent

1. In the top navigation menuClick **智能体管理**
2. For the agent linked to the devices,Click **Edit Agent**
3. In the right-hand details panel,，Click **Edit Functions**
4. Enable **Device-to-device Call** 工具
5. Click **Save Configuration** to confirm
6. In the main agent panel, alsoClick **Save Configuration** ，then restart the device

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
    ```
5. Follow [Firmware Build Guide](firmware-build.md) to build and flash the device
6. Enable AEC in firmware configuration even on a single-microphone device!
7. Enable AEC in firmware configuration even on a single-microphone device!
8. Enable AEC in firmware configuration even on a single-microphone device!

### Step 5. Set up the MQTT gateway

1. Deploy the gateway following [MQTT gateway integration](mqtt-gateway-integration.md)
2. If already deployed, check the gateway version isMay 27, 2026or later

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

### Q: 如何to confirmAddress Book功能已开启？

- management console顶部菜单如显示"Address Book"入口，则表示已开启

### Q: ASR mishears the contact nickname. How do I fix this?
- Check whether your ASR provider supports hotwords.
- If using`FunASRServer`,add the correct nickname to the`hotword file`and restart the container.
- If using`Volcengine` service，you can`Volcengine provider console` add`hotword file`，then return tomanagement console的`Model Configuration`，and set`hotword table name`under`Volcengine的tts`as appropriate。

