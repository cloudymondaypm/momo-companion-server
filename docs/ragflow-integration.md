# RAGFlow Knowledge Base Integration

This guide explains how to deploy [RAGFlow](https://github.com/infiniflow/ragflow) using existing MySQL/Redis services, connect it to Momo Companion's management console, and attach a knowledge base to an agent. If you already run RAGFlow, skip to [Configure the Management Console](#part-2-configure-the-management-console).

## Part 1. Deploy RAGFlow

### 1. Verify MySQL and Redis connectivity

RAGFlow needs a database and Redis. You can reuse the services installed by the full Momo Companion deployment if they are accessible to the RAGFlow container:

```bash
telnet 127.0.0.1 3306
telnet 127.0.0.1 6379
```

Replace localhost with the actual service host. If the services run in Docker, prefer a shared private Docker network. As an alternative, configure host port publishing in your `docker-compose_all.yml`:

```yaml
services:
  xiaozhi-esp32-server-db:
    ports:
      - "3306:3306"
  xiaozhi-esp32-server-redis:
    ports:
      - "6379:6379"
```

**Security:** Port publishing may make the database and Redis accessible beyond the Docker network. Restrict firewall access to trusted hosts; do not expose unauthenticated Redis to the public internet. Back up persistent data before restarting database containers.

### 2. Create a dedicated MySQL database

Connect to MySQL and execute:

```sql
CREATE DATABASE IF NOT EXISTS rag_flow
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'rag_flow'@'%' IDENTIFIED BY 'YOUR_STRONG_RAGFLOW_PASSWORD';
GRANT ALL PRIVILEGES ON rag_flow.* TO 'rag_flow'@'%';
FLUSH PRIVILEGES;
```

Use the same strong password in your RAGFlow environment settings.

### 3. Download RAGFlow

The original integration instructions were tested with version `v0.22.0`. Check the [RAGFlow release documentation](https://github.com/infiniflow/ragflow) before applying these steps to other versions.

```bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow
git checkout v0.22.0
cd docker
```

Edit `docker-compose.yml` to remove the MySQL `depends_on` dependency for `ragflow-cpu` and/or `ragflow-gpu` if you use an external MySQL service. In `docker-compose-base.yml`, remove the bundled `mysql` and `redis` services so they are not launched twice; retain RAGFlow's other required services (for example, MinIO).

### 4. Configure RAGFlow environment variables

Edit `ragflow/docker/.env`. Ensure **`MYSQL_USER` is explicitly present**; it may be missing from some versions of the example file:

```dotenv
SVR_WEB_HTTP_PORT=8008
SVR_WEB_HTTPS_PORT=8009

MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_USER=rag_flow
MYSQL_PASSWORD=YOUR_STRONG_RAGFLOW_PASSWORD
MYSQL_DBNAME=rag_flow

REDIS_HOST=host.docker.internal
REDIS_PORT=6379
REDIS_PASSWORD=
```

`host.docker.internal` may require additional Docker configuration on Linux, such as an `extra_hosts` entry mapping it to `host-gateway`, or you can use a reachable database hostname on your network.

If Redis has no password, check `service_conf.yaml.template` and ensure its default does not silently insert a different password:

```yaml
redis:
  db: 1
  password: '${REDIS_PASSWORD:-}'
  host: '${REDIS_HOST:-redis}:6379'
```

For production, enable Redis authentication rather than leaving it open.

### 5. Start the RAGFlow containers

```bash
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml logs -f --tail=20
```

Check the logs for database, Redis, and model initialization errors.

### 6. Register a RAGFlow user

Open `http://127.0.0.1:8008` (or your configured host), select **Sign Up**, and create an account. Sign in to confirm the service is working.

You may disable public registration in `.env` after creating your account:

```dotenv
REGISTER_ENABLED=0
```

Restart the affected containers to apply that change.

### 7. Configure RAGFlow's LLM and embedding model

After signing in, open the profile/avatar settings and choose **Model Providers**. Add an API key for an LLM and a **Text Embedding** provider, then choose the default LLM and embedding model.

Verify that each provider key has access to the selected model and that the embedding vector dimensions are compatible with your RAGFlow database configuration.

## Part 2. Configure the Management Console

### 1. Obtain the RAGFlow API key

In RAGFlow, open your avatar/settings → **API** → **API Key** → **Create New Key**. Copy the key.

### 2. Connect RAGFlow to Momo Companion

The upstream guide requires management console version `0.8.7` or newer.

1. Sign in as superadmin.
2. Open **Parameter Dictionary → System Feature Configuration**, enable **Knowledge Base**, and save.
3. Open **Model Configuration → Knowledge Base**.
4. Find `RAG_RAGFlow` and select **Edit**.
5. Enter the RAGFlow **Service URL**, for example `http://192.168.1.100:8008` (a host reachable by the management API).
6. Paste the RAGFlow **API Key** and save.

### 3. Create and populate a knowledge base

1. Open **Knowledge Base** and click **Add**.
2. Enter a descriptive name and summary, such as **Company Information** and **Company history, services, contact details and business address**.
3. Save and open the new knowledge base.
4. Upload your documents, then click **Parse** to extract searchable chunks.
5. Review the chunk data and run **Retrieval Test** to verify that relevant queries return the expected material.

### 4. Attach the knowledge base to an agent

Open **Agent Management**, select an agent, and choose **Agent Configuration → Edit Functions**. Enable or select the relevant knowledge base and save.

The agent should now be able to use the RAGFlow integration when responding to knowledge-base questions.
