import pytest
import requests
import base64
import json

def test_missing_auth_header(client):
    """Verify proxy returns 401 if requester does not send any Auth header"""
    response = client.get("/proxy")

    assert response.status_code ==  401
    assert response.json["error"] == "Missing Authorization header"

def test_invalid_auth_header_scheme(client):
    """Verify proxy returns 401 if requester sends non-Basic Auth header"""
    token = "definitely_not_a_fake_token_123"

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code ==  401
    assert response.json["error"] == "Invalid Authorization scheme"

def test_username_only_auth_header(client):
    """
    Verify proxy returns 401 if requester sends username-only Basic Auth header
    (e.g. if sending API key via Basic auth instead of username:password)
    """
    credentials = base64.b64encode("username".encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {credentials}"}
    )

    assert response.status_code == 401
    assert response.json["error"] == "Invalid credentials format"

def test_decode_and_forward_basic_auth(client, mock_ragnar_api):
    """
    Verify proxy successfully decodes and forwards Basic Auth header
    1) Verify that mock API returns 200 and payload
    2) Verify that decoded credentials forwarded to mock API match raw inputs
    """
    # Mock GET /api/auth/status
    # (Return unauthenticated to force login flow)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/auth/status",
        json={"authenticated": False},
        status=200,
    )

    # Mock POST /api/auth/login
    # (Handle authentication request)
    mock_ragnar_api.add(
        mock_ragnar_api.POST,
        "https://ragnar.test.local/api/auth/login",
        json={"status": "authenticated"},
        status=200,
    )

    # Mock GET /api/status
    # (Return final proxy payload)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/status",
        json={"status": "ok"}, # placeholder for actual API data
        status=200,
    )

    raw_username = "user_name"
    raw_password = "p@$$w0rd:w1th:C0L0NS!"
    raw_credentials = f"{raw_username}:{raw_password}"
    encoded_credentials = base64.b64encode(raw_credentials.encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {encoded_credentials}"}
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

    # Extract the authentication POST request made to mock API
    login_call = next(
        call for call in mock_ragnar_api.calls 
        if call.request.url == "https://ragnar.test.local/api/auth/login"
    )

    # Verify that decoded base64 credentials match raw credentials
    payload = json.loads(login_call.request.body)
    assert payload["username"] == raw_username
    assert payload["password"] == raw_password

def test_creds_not_sent_if_already_authenticated(client, mock_ragnar_api):
    """
    Test proxy workflow when session is already authenticated via session cookie
    1) Verify mock API returns status 200 and payload
    2) Verify client credentials are not forwarded to mock API
    """
    # Mock GET /api/auth/status
    # (Return authenticated to bypass login flow)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/auth/status",
        json={"authenticated": True},
        status=200,
    )

    # Mock GET /api/status
    # (Return final proxy payload)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/status",
        json={"status": "ok"}, # placeholder for actual API data
        status=200,
    )

    credentials = "username:password"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {encoded_credentials}"}
    )

    # Verify response status code and payload received
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

    # Verify authentication POST request was not made to mock API
    login_call = any(
        call for call in mock_ragnar_api.calls 
        if call.request.url == "https://ragnar.test.local/api/auth/login"
    )
    assert not login_call

def test_invalid_login_credentials(client, mock_ragnar_api):
    """Verify proxy returns 401 when invalid credentials are provided"""
    # Mock GET /api/auth/status
    # (Return unauthenticated to force login flow)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/auth/status",
        json={"authenticated": False},
        status=200,
    )

    # Mock POST /api/auth/login
    # (Return 401 Unauthorized)
    ragnar_error_message = "Invalid username or password"
    mock_ragnar_api.add(
        mock_ragnar_api.POST,
        "https://ragnar.test.local/api/auth/login",
        body=ragnar_error_message,
        status=401,
    )

    credentials = "bad_username:bad_password"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {encoded_credentials}"}
    )

    # Verify 401 status code and error message are returned
    assert response.status_code == 401

    data = response.get_json()
    assert data["error"] == "Ragnar login failed"
    assert "HTTP 401" in data["details"]
    assert ragnar_error_message in data["details"]

def test_ragnar_auth_unreachable(client, mock_ragnar_api):
    """
    Verify proxy returns 500 when proxy is unable to authenticate because Ragnar is unreachable
    (e.g. server down, DNS resolution issue, timeout)
    """
    # Simulate /api/auth/status endpoint unreachable
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/auth/status",
        body=requests.exceptions.ConnectTimeout("Host unreachable"),
    )
    # If auth status check fails, proxy will attempt to authenticate
    # Simulate /api/auth/login endpoint unreachable
    mock_ragnar_api.add(
        mock_ragnar_api.POST,
        "https://ragnar.test.local/api/auth/login",
        body=requests.exceptions.ConnectTimeout("Host unreachable"),
    )

    credentials = "username:password"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {encoded_credentials}"}
    )

    assert response.status_code == 500
    assert "Ragnar login failed" in response.get_json()["error"]

def test_ragnar_data_unreachable(client, mock_ragnar_api):
    """
    Verify proxy returns 502 when authenticated but Ragnar data endpoint is unreachable
    (e.g. server down, DNS resolution issue, timeout)
    """
    # Simulate proxy session already authenticated
    # (assume /api/auth/status is reachable but /api/status is not)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/auth/status",
        json={"authenticated": True},
        status=200,
    )
    # Simulate /api/status endpoint unreachable
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/status",
        body=requests.exceptions.ConnectTimeout("Host unreachable"),
    )

    credentials = "username:password"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {encoded_credentials}"}
    )

    assert response.status_code == 502
    assert "Failed to fetch data from Ragnar" in response.get_json()["error"]

def test_ragnar_application_error(client, mock_ragnar_api):
    """
    Verify proxy returns 500 when authenticated but Ragnar
    data endpoint returns application error
    """
    # Simulate proxy session already authenticated
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/auth/status",
        json={"authenticated": True},
        status=200,
    )
    # Simulate /api/status endpoint returns 500
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "https://ragnar.test.local/api/status",
        json={"error": "Internal application error"},
        status=500
    )

    credentials = "username:password"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    response = client.get(
        "/proxy",
        headers={"Authorization": f"Basic {encoded_credentials}"}
    )

    assert response.status_code == 502
    data = response.get_json()
    assert "Failed to fetch data from Ragnar" in data["error"]
    assert "500" in data["details"]