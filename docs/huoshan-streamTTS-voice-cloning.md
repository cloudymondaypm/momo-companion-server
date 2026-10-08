# Volcengine Bidirectional Streaming TTS and Voice Cloning

This guide covers four phases: preparation, service configuration, voice cloning, and selecting the cloned voice for an agent in the management console.

## Phase 1. Prepare the Volcengine account

The superadministrator must first activate Volcengine services and obtain the **App ID**, **Access Token**, and voice resource IDs. The provider may include an initial voice resource; additional resources may need to be purchased separately.

### 1. Activate the service

Open the [Volcengine Speech App Console](https://console.volcengine.com/speech/app), create an application, and activate the large-model speech synthesis and voice cloning services.

### 2. Copy voice resource information

Visit the [voice resources page](https://console.volcengine.com/speech/service/9999). Record:

- App ID
- Access Token
- Voice resource ID, typically in the form `S_xxxxx`

![Get a voice resource ID](images/image-clone-integration-01.png)

Each voice resource may be assigned to a separate account in Momo Companion.

## Phase 2. Configure Volcengine in the management console

### 1. Configure TTS credentials

Sign in as superadmin. Open **Model Configuration → Text to Speech**, select **Volcengine Bidirectional Streaming TTS**, and click **Edit**.

Enter the Volcengine **App ID** in **Application ID** and the **Access Token** in **Access Token**. Save.

### 2. Enable voice cloning and assign resources

Open **Parameter Dictionary → System Feature Configuration**, enable **Voice Cloning**, and save. The **Voice Cloning** menu should become available.

Open **Voice Cloning → Voice Resources**, click **Add**, and:

1. Choose **Volcengine Bidirectional Streaming TTS** as the provider.
2. Enter the voice resource ID (`S_xxxxx`).
3. Choose the account that owns this resource (you may assign it to your own account).
4. Save.

## Phase 3. Clone a voice

Open **Voice Cloning → Voice Cloning**.

If you see a message saying your account has no voice resources, ask the superadministrator to assign a resource in Phase 2.

Otherwise select a resource, click **Upload Audio**, and upload the reference voice recording. Preview the audio and trim it as needed, then confirm the upload.

![Upload reference audio](images/image-clone-integration-02.png)

The voice should enter **Pending Cloning** status. Click **Clone Now** and inspect the result. If cloning fails, hover over the error icon to view the provider's error message.

After successful training, the status becomes **Training Succeeded**. Rename the voice to make it easier to find later.

Only clone voices you own or have permission to reproduce.

## Phase 4. Use the cloned voice

1. Open **Agent Management** and select an agent.
2. Click **Agent Configuration**.
3. Set TTS to **Volcengine Bidirectional Streaming TTS**.
4. Select the resource labeled as a **Cloned Voice**.
5. Save the agent.

![Select cloned voice](images/image-clone-integration-03.png)

Wake Momo Companion to test the voice. Make sure the selected voice supports your desired speaking language.
