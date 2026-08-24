# ragnar-api-proxy

Ragnar API Proxy is a simple, lightweight proxy for [PierreGode/Ragnar](https://github.com/PierreGode/Ragnar). It was developed with [gethomepage/homepage](https://github.com/gethomepage/homepage) in mind but supports any application that uses HTTP basic authentication headers.

## Overview

Ragnar is a powerful network scanning tool which can be used for monitoring and vulnerability assessment. It ships with an API enabling retrieval of Ragnar's data which is unsecured by default. If the user enables authentication, API access is authenticated via a Flask session cookie, which is received by the client after `POST`ing login credentials (username/password) to its authentication endpoint.

This authentication flow is incompatible with stateless clients such as Homepage. A middleware service is required to proxy the API requests and handle session cookie management. That's where Ragnar API Proxy comes in. It enables a client like Homepage to send a request via a HTTP basic authentication header and receive the JSON returned by Ragnar's `/api/auth` endpoint.

## Features

- Simple and lightweight
- Enables stateless clients to authenticate Ragnar API Proxy
    - Supports clients that can send a HTTP Basic Auth header
- Only forwards Ragnar login credentials when a new session cookie is needed
- Supports HTTP/HTTPS Ragnar servers
- Lightweight Docker image for quick deployment and easy integration with Homepage or other applications

## Project Structure

```
.
├── examples
│   ├── docker
│   │   ├── compose-standalone.yml      # Standalone Docker installation
│   │   └── compose-homepage.yml        # Deployment with Homepage
│   └── systemd
│       └── ragnar-api-proxy.service    # Systemd unit file for non-Docker installation
├── src
│   ├── __init__.py
│   └── app.py              # Main entrypoint
├── tests
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   └── test_routes.py      # Main test module
├── compose.yml.example     # Sample Docker Compose
├── Dockerfile              # Docker image definition
├── gunicorn.conf.py        # Gunicorn configuration
├── README.md               # Documentation
├── requirements-dev.txt    # Python dependencies (development/testing)
├── requirements.txt        # Python dependencies (production)
├── .dockerignore           # Docker image build context exclusions
└── .env.example            # Sample environment variables
```

## Installation

### Method 1: Docker Compose (Recommended)

### Method 2: Build from Source

## Configuration

### Homepage