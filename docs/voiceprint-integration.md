# Enable Voiceprint Recognition

This guide covers deployment of the standalone voiceprint recognition API and its configuration for either the full management console or the standalone AI server.

## 1. Deploy the voiceprint API

### Step 1. Download the API server

Open the upstream [voiceprint-api repository](https://github.com/xinnan-tech/voiceprint-api). Clone it or download the ZIP archive and extract it as `voiceprint-api`.

### Step 2. Prepare MySQL access

Voiceprint recognition requires a MySQL database. If you already use the full management system, you may reuse its MySQL server.

Test connectivity from the system running the voiceprint service:

```bash
telnet 127.0.0.1 3306
```

Replace `127.0.0.1` with the database host if MySQL runs elsewhere.

If MySQL is in Docker and the voiceprint container cannot reach it, prefer placing both services on a **shared Docker network**. Alternatively, publish port 3306 on a trusted private interface in the database Compose service:

```yaml
services:
  xiaozhi-esp32-server-db:
    ports:
      - "3306:3306"
```

Publishing a database port can expose it to networks that should not have access. Limit the binding and firewall rules to trusted hosts, and use a password-protected MySQL account. After adjusting the Compose file, restart the affected service according to your deployment configuration and verify connectivity.

### Step 3. Create the database and table

Connect to MySQL and run:

```sql
CREATE DATABASE voiceprint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE voiceprint_db;

CREATE TABLE voiceprints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    speaker_id VARCHAR(255) NOT NULL UNIQUE,
    feature_vector LONGBLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_speaker_id (speaker_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Step 4. Configure database access

In the `voiceprint-api` directory create a `data` folder and copy `voiceprint.yaml` into it as `.voiceprint.yaml`.

Edit the MySQL settings:

```yaml
mysql:
  host: "192.168.1.25"
  port: 3306
  user: "root"
  password: "YOUR_DATABASE_PASSWORD"
  database: "voiceprint_db"
```

Set `host` to a database address reachable **from inside the voiceprint API container**. Docker localhost normally refers to the container itself. For production, consider a dedicated MySQL account with access only to `voiceprint_db` rather than the root account.

### Step 5. Start the service

Docker deployment is recommended; refer to the upstream [source installation guide](https://github.com/xinnan-tech/voiceprint-api/blob/main/README.md) for other methods.

```bash
cd voiceprint-api

# Optional cleanup of old containers
docker compose -f docker-compose.yml down
docker stop voiceprint-api
docker rm voiceprint-api
docker rmi ghcr.nju.edu.cn/xinnan-tech/voiceprint-api:latest

# Start the API
docker compose -f docker-compose.yml up -d
docker logs -f voiceprint-api
```

Logs should show an HTTP endpoint on port 8005, for example:

```text
Voiceprint endpoint: http://127.0.0.1:8005/voiceprint/health?key=abcd
```

Replace localhost with a hostname or IP reachable by the AI server or management console, for example:

```text
http://192.168.1.25:8005/voiceprint/health?key=abcd
```

Open it in a browser and confirm a healthy response:

```json
{"total_voiceprints":0,"status":"healthy"}
```

Keep the full URL and authentication key private.

## 2. Full management console deployment

### Step 1. Enable and connect the voiceprint service

1. Sign in as administrator.
2. Open **Parameter Dictionary → System Feature Configuration**, enable **Voiceprint Recognition**, and save.
3. Open **Parameter Dictionary → Parameter Management** and find `server.voice_print`.
4. Set its value to the voiceprint health endpoint from Step 5 above and save.

If the console rejects the URL, check that the service is running and that the network and firewall allow communication.

### Step 2. Configure the agent's memory and history

In the target agent's configuration, select **Local Short-Term Memory** and enable **Text + Audio reporting**.

### Step 3. Record and register a speaker

Turn on the device and talk in your normal speaking voice. In **Agent Management**, open the agent's **Voiceprint Recognition** panel and choose **Add** to register a speaker from the recorded conversation.

An optional description can capture details useful to the agent, such as a speaker's occupation or interests. Do not add sensitive personal information without the speaker's consent.

### Step 4. Test

Talk to the assistant and ask, **"Do you know who I am?"** Confirm that it identifies the registered speaker as expected.

## 3. Standalone xiaozhi-server

### Step 1. Configure the voiceprint service

Add this to `main/xiaozhi-server/data/.config.yaml`, replacing the URL with your reachable API endpoint:

```yaml
voiceprint:
  url: http://192.168.1.25:8005/voiceprint/health?key=YOUR_KEY
  speakers:
    - "test1,Alex,Alex is a programmer"
    - "test2,Jamie,Jamie is a product manager"
    - "test3,Sam,Sam is a designer"
```

Each `speaker_id` must correspond to a speaker registered with the voiceprint API.

### Step 2. Register voiceprints

View API documentation at `http://localhost:8005/voiceprint/docs` if accessible on the API host.

The registration endpoint accepts an authenticated `POST` request with `speaker_id` and a WAV audio file. The bearer token is the value after `?key=` in the voiceprint health URL.

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "speaker_id=test1" \
  -F "file=@/path/to/speaker.wav" \
  http://localhost:8005/voiceprint/register
```

Make sure `speaker_id` matches the identifier in `.config.yaml` and that the recording comes from the same speaker.

### Step 3. Start and verify

Start both the voiceprint API and Momo Companion server. Once the speaker is registered, ask the assistant who is speaking and review the voiceprint logs if the result is unexpected.
