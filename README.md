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
│       └── ragnar-api-proxy.service    # Systemd unit file for non-Docker deployment
├── src
│   ├── __init__.py
│   └── app.py                          # Main entrypoint
├── tests
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   └── test_routes.py                   # Main test module
├── Dockerfile                           # Docker image definition
├── gunicorn.conf.py                     # Gunicorn configuration
├── README.md                            # Documentation
├── requirements-dev.txt                 # Python dependencies (development/testing)
├── requirements.txt                     # Python dependencies (production)
├── .dockerignore                        # Docker image build context exclusions
└── .env.example                         # Sample environment variables
```

## Installation

### Method 1: Docker Compose (Recommended)

**Step 0: Create Directory for Ragnar API Proxy**

```bash
mkdir /opt/ragnar-api-proxy
cd /opt/ragnar-api-proxy
```

**Step 1: Clone Repository**

```bash
git clone https://github.com/jark-dev/ragnar-api-proxy.git
```

**Step 2: Configure Environment Variables**

Copy `.env.example` to `.env`.

```bash
cp .env.example .env
```

If deploying alongside the client service (e.g. Homepage) in a single Docker stack, `LISTEN_ADDRESS` should be set to `0.0.0.0` so that Ragnar API Proxy is accessible over the Docker network. This configuration also supports cases where the client service runs outside the Docker network.

```env
#.env
LISTEN_ADDRESS=0.0.0.0
```

The default `LISTEN_PORT` of `5000` works fine for most setups, but this can be modified if desired.

```env
#.env
LISTEN_PORT=5000
```

Update `RAGNAR_BASE_URL` to reflect your setup. Be sure to include the leading `http://` or `https://` and the trailing port (e.g. `:8000`) if your setup does not use standard HTTP(S) ports (80 for HTTP and 443 for HTTPS). Port 8000 is standard for most Ragnar installations. Do not include a trailing slash.

```env
#.env
RAGNAR_BASE_URL=http://ragnar.example.org:8000
```

If using Ragnar with a custom HTTPS certificate, uncomment `REQUESTS_CA_BUNDLE` and set its value to the path of your custom certificate chain (including the CA certificate and leaf certificate).

```env
#.env
RAGNAR_BASE_URL=https://ragnar.example.org:8000
REQUESTS_CA_BUNDLE=/path/to/custom-ca-chain.pem
```

### Method 2: Build from Source

## Configuration

### Homepage
