# ragnar-api-proxy

Ragnar API Proxy is a simple, lightweight proxy for [PierreGode/Ragnar](https://github.com/PierreGode/Ragnar). It was developed with [gethomepage/homepage](https://github.com/gethomepage/homepage) in mind but supports any application that uses HTTP basic authentication headers.

## Overview

Ragnar is a powerful network scanning tool which can be used for monitoring and vulnerability assessment. It ships with an API enabling retrieval of Ragnar's data which is unsecured by default. If the user enables authentication, API access is authenticated via a Flask session cookie, which is received by the client after `POST`ing login credentials (username/password) to its authentication endpoint.

This authentication flow is incompatible with stateless clients such as Homepage. A middleware service is required to proxy the API requests and handle session cookie management. That's where Ragnar API Proxy comes in. It enables a client like Homepage to send a request via a HTTP basic authentication header and receive the JSON returned by Ragnar's `/api/auth` endpoint.

## Features

- Simple and lightweight
- Enables stateless clients to authenticate Ragnar API Proxy
  - Designed with Homepage in mind
  - Supports clients that can send a HTTP Basic Auth header
- Only forwards Ragnar login credentials when a new session cookie is needed
- Supports HTTP/HTTPS Ragnar servers
- Lightweight Docker image for quick deployment and easy integration with Homepage or other applications

## Project Structure

```text
.
├── examples
│   ├── docker
│   │   ├── compose-standalone.yml      # Standalone Docker deployment
│   │   └── compose-homepage.yml        # Docker deployment alongside Homepage
│   └── systemd
│       └── ragnar-api-proxy.service    # Systemd service file for non-Docker deployment
├── src
│   ├── __init__.py
│   └── app.py                          # Main entrypoint
├── tests
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   └── test_routes.py                  # Main test module
├── Dockerfile                          # Docker image definition
├── gunicorn.conf.py                    # Gunicorn configuration
├── README.md                           # Documentation
├── requirements-dev.txt                # Python dependencies (development/testing)
├── requirements.txt                    # Python dependencies (production)
├── .dockerignore                       # Docker image build context exclusions
└── .env.example                        # Sample environment variables
```

## Installation

### Method 1: Docker Compose (Recommended)

#### Step 0: Create Directory for Ragnar API Proxy

```bash
mkdir /opt/ragnar-api-proxy
cd /opt/ragnar-api-proxy
```

#### Step 1: Clone Repository

```bash
git clone https://github.com/jark-dev/ragnar-api-proxy.git
```

#### Step 2: Configure Environment Variables

Copy `.env.example` to `.env`.

```bash
cp .env.example .env
```

For all Docker deployments, `LISTEN_ADDRESS` should be kept at the default value of `0.0.0.0`. This applies to configurations where the client service (e.g. Homepage) is deployed within the same Docker network as Ragnar API Proxy, as well as configurations where the client service is deployed outside the Docker network.

> [!NOTE]
> **This listen address applies only to the Flask app running inside the Docker container. The listen address of the Docker container is specified in the Compose file via the `expose` or `ports` attributes (next section).**

```env
# .env
LISTEN_ADDRESS=0.0.0.0
```

The default `LISTEN_PORT` of `5000` works fine for most setups, but this can be modified if desired.

```env
# .env
LISTEN_PORT=5000
```

Update `RAGNAR_BASE_URL`. Be sure to include the leading `http://` or `https://`. Also include the trailing port (e.g. `:8000`) if your setup does not use standard HTTP(S) ports (80 for HTTP and 443 for HTTPS). Port 8000 is standard for most Ragnar installations. Do not include a trailing slash.

```env
# .env
RAGNAR_BASE_URL=http://ragnar.example.org:8000
```

If using Ragnar with a custom HTTPS certificate, uncomment `REQUESTS_CA_BUNDLE` and set its value to the path of your custom certificate chain (including the CA certificate and leaf certificate). If using HTTP or a non-custom HTTPS certificate (e.g. Let's Encrypt), leave `REQUESTS_CA_BUNDLE` commented out (or delete it).

```env
#.env
RAGNAR_BASE_URL=https://ragnar.example.org:8000
REQUESTS_CA_BUNDLE=/path/to/custom-ca-chain.pem
```

> [!IMPORTANT]
> **If the client service runs on a remote host, it is strongly recommended to use HTTPS as HTTP Basic Auth transmits Ragnar login credentials in base64-encoded cleartext (i.e. unencrypted). If HTTP absolutely must be used, it is highly recommended to run Ragnar API proxy and the client service on the same host to minimize the potential attack surface.**

#### Step 3: Configure Compose File

Copy the appropriate Compose file example from the `/examples` subdirectory to the root of the working directory as `compose.yml`.

For deployment alongside Homepage in a single Compose file, copy the `compose-homepage.yml` example.

```bash
cp ./examples/compose-homepage.yml compose.yml
```

Replace the `homepage` section in the `services` block with your configuration.

```yaml
# compose.yml
compose-homepage.yml
```

For standalone deployment, copy the `compose-standalone.yml` example.

```bash
cp ./examples/compose-standalone.yml compose.yml
```

By default, the container will listen only on `localhost`, which is preferred when the client is running on the same host. If the client runs on a remote host, replace the leading `127.0.0.1` in the `ports` attribute with the desired listen address (e.g. 0.0.0.0 or a specific address).

```yaml
# compose.yml
compose-standalone.yml
```

#### Step 4: Start Ragnar API Proxy

Create and start the service using Docker Compose.

```bash
docker compose up -d
```

### Method 2: Build from Source

#### Step 0: Create Directory for Ragnar API Proxy

```bash
mkdir /opt/ragnar-api-proxy
cd /opt/ragnar-api-proxy
```

#### Step 1: Clone Repository

```bash
git clone https://github.com/jark-dev/ragnar-api-proxy.git
```

#### Step 2: Create and Activate Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

Copy `.env.example` to `.env`.

```bash
cp .env.example .env
```

Configure the `LISTEN_ADDRESS` according to the desired setup:

| Location of Client Service    | `LISTEN_ADDRESS`                   |
|-------------------------------|------------------------------------|
| Same host as Ragnar API Proxy | `127.0.0.1`                        |
| Remote host                   | `0.0.0.0` (or specific IP address) |

```env
# .env
LISTEN_ADDRESS=0.0.0.0
```

The default `LISTEN_PORT` of `5000` works fine for most setups, but this can be modified if desired.

```env
# .env
LISTEN_PORT=5000
```

Update `RAGNAR_BASE_URL`. Be sure to include the leading `http://` or `https://`. Also include the trailing port (e.g. `:8000`) if your setup does not use standard HTTP(S) ports (80 for HTTP and 443 for HTTPS). Port 8000 is standard for most Ragnar installations. Do not include a trailing slash.

```env
# .env
RAGNAR_BASE_URL=http://ragnar.example.org:8000
```

If using Ragnar with a custom HTTPS certificate, uncomment `REQUESTS_CA_BUNDLE` and set its value to the path of your custom certificate chain (including the CA certificate and leaf certificate). If using HTTP or a non-custom HTTPS certificate (e.g. Let's Encrypt), leave `REQUESTS_CA_BUNDLE` commented out (or delete it).

```env
#.env
RAGNAR_BASE_URL=https://ragnar.example.org:8000
REQUESTS_CA_BUNDLE=/path/to/custom-ca-chain.pem
```

> [!IMPORTANT]
> **If the client service runs on a remote host, it is strongly recommended to use HTTPS as HTTP Basic Auth transmits Ragnar login credentials in base64-encoded cleartext (i.e. unencrypted). If HTTP absolutely must be used, it is highly recommended to run Ragnar API proxy and the client service on the same host to minimize the potential attack surface.**

#### Step 5: Start Ragnar API Proxy

Ragnar API Proxy can be executed in the command line via the following command:

```bash
gunicorn "src.app:create_app()"
```

#### Step 6 (Optional): Run Ragnar API Proxy as a systemd Service

The command above works fine for testing, but for production, it is recommended (and more convenient) to run Ragnar API Proxy as a daemon. This can be achieved by creating a systemd unit. Copy the systemd service file example to `/etc/systemd/system`.

```bash
cp ./examples/systemd/ragnar-api-proxy.service /etc/systemd/system/ragnar-api-proxy.service
```

The default service file works out of the box, assuming that the working directory is `/opt/ragnar-api-proxy`. If a custom working directory was used, replace all instances of `/opt/ragnar-api-proxy` with the appropriate path in `WorkingDirectory=` and `ExecStart=`.

Additionally, the service will run as `www-data` by default. This is appropriate for systems where Ragnar API Proxy is the only application running as this user. If the system has other applications also running as `www-data`, consider creating a dedicated user for Ragnar API Proxy to maximize isolation. Replace `www-data` with the custom user in `User=` and `Group=`.

```text
# /etc/systemd/system/ragnar-api-proxy.service
[Unit]
Description=Gunicorn instance serving Ragnar API Proxy
After=network.target

[Service]
User=your-username
Group=your-username
WorkingDirectory=/path/to/ragnar-api-proxy
ExecStart=/path/to/ragnar-api-proxy/.venv/bin/gunicorn --config /path/to/ragnar-api-proxy/gunicorn.conf.py "src.app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

Ensure the configured user has read permissions for the working directory. The easiest way to achieve this is to recursively `chown` the working directory. Remember to update the user and group name to the custom user if the default `www-data` is not used.

```bash
chown -R www-data:www-data /opt/ragnar-api-proxy
```

Enable and start the service.

```bash
systemctl daemon-reload
systemctl enable ragnar-api-proxy.service
systemctl start ragnar-api-proxy.service
systemctl status ragnar-api-proxy.service  # verify service started successfully
```

## Configuration

### Homepage

### Other Services

Currently, official configuration documentation only exists for Homepage, but Ragnar API Proxy is compatible with any service that uses HTTP Basic Auth headers to access external APIs. The high-level configuration steps are as follows:

1. Point the service to Ragnar API Proxy's endpoint
    - Default: `http://ragnar.example.org:8000/proxy`
