# Build Docker Images From Source

GitHub Actions can build release images automatically. You only need this guide if you changed the source code and want to deploy your own custom Docker images.

## 1. Install Docker

Install Docker Engine and the Compose/Buildx plugins using the instructions for your Linux distribution. On Ubuntu or Debian, after configuring Docker's official package repository, the packages can be installed with:

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 2. Build the server and web images

Choose a Docker Hub username (or your preferred image namespace) and a **new version tag** such as `1.2.3` or `20261008`. Use a unique tag so you can distinguish builds and roll back when necessary.

From the repository root (where the Dockerfiles are located), run:

```bash
# Build the server image
docker build -f Dockerfile-server -t YOUR_DOCKERHUB_USER/xiaozhi-esp32-server:YOUR_VERSION .

# Build the web/management image
docker build -f Dockerfile-web -t YOUR_DOCKERHUB_USER/xiaozhi-esp32-server-web:YOUR_VERSION .
```

Keep the internal image/service names unless you also update the Compose configuration; the upstream identifiers are used by existing deployment scripts.

## 3. Update Docker Compose

```bash
cd main/xiaozhi-server
```

Edit `docker-compose_all.yml` to point to the two images you just built:

```yaml
services:
  xiaozhi-esp32-server:
    image: YOUR_DOCKERHUB_USER/xiaozhi-esp32-server:YOUR_VERSION
    # Keep the other existing settings

  xiaozhi-esp32-server-web:
    image: YOUR_DOCKERHUB_USER/xiaozhi-esp32-server-web:YOUR_VERSION
    # Keep the other existing settings
```

## 4. Restart the services

```bash
# Stop the old containers
docker compose -f docker-compose_all.yml down

# Start the new containers
docker compose -f docker-compose_all.yml up -d
```

## 5. Verify startup

```bash
# Follow server logs
docker logs -f -n 50 xiaozhi-esp32-server

# Follow management logs
docker logs -f -n 50 xiaozhi-esp32-server-web
```

Verify that both containers start and the device can reconnect to the server.
