import pytest
import responses
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
    1) Verify that mock API returns 200
    2) Verify that decoded credentials forwarded to mock API match raw inputs
    """
    # Mock GET /api/auth/status
    # (Return unauthenticated to force login flow)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "http://ragnar.test.local/api/auth/status",
        json={"authenticated": False},
        status=200,
    )

    # Mock POST /api/auth/login
    # (Handle authentication request)
    mock_ragnar_api.add(
        mock_ragnar_api.POST,
        "http://ragnar.test.local/api/auth/login",
        json={"status": "authenticated"},
        status=200,
    )

    # Mock GET /api/status
    # (Return final proxy payload)
    mock_ragnar_api.add(
        mock_ragnar_api.GET,
        "http://ragnar.test.local/api/status",
        json={"status": "ok"},
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

    # Extract the authentication POST request made to mock API
    login_call = next(
    call for call in mock_ragnar_api.calls 
    if call.request.url == "http://ragnar.test.local/api/auth/login"
    )

    # Verify that decoded base64 credentials match raw credentials
    payload = json.loads(login_call.request.body)
    assert payload["username"] == raw_username
    assert payload["password"] == raw_password