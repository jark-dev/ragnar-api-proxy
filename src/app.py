import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify

def create_app(config=None):

    # Initialize Flask app
    app = Flask(__name__)

    # Load default config
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Define environment variables
    app.config["LISTEN_ADDRESS"] = os.getenv("LISTEN_ADDRESS", "127.0.0.1")
    app.config["LISTEN_PORT"] = os.getenv("LISTEN_PORT", "5000")
    app.config["RAGNAR_BASE_URL"] = os.getenv("RAGNAR_BASE_URL", "http://localhost:8000")

    # Override with test config if provided
    if config:
        app.config.update(config)

    # Initialize session (persists across requests and stores session cookie)
    ragnar_session = requests.Session()

    def is_authenticated():
        """
        Checks RAGNAR_AUTH_CHECK_ENDPOINT using global session.
        Returns True if authentication is confirmed
        """
        try:
            resp = ragnar_session.get(f"{app.config['RAGNAR_BASE_URL']}/api/auth/status")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("authenticated") is True
            return False
        except requests.exceptions.RequestException:
            return False

    def authenticate_ragnar(username, password):
        """
        Forwards username/password to RAGNAR_LOGIN_ENDPOINT using global session.
        Session object captures and stores Set-Cookie header
        """
        try:
            resp = ragnar_session.post(
                f"{app.config['RAGNAR_BASE_URL']}/api/auth/login",
                json={"username": username, "password": password}
            )

            # Check for HTTP errors (4xx, 5xx)
            if resp.status_code == 200:
                return True, resp.status_code, None
            else:
                # Return status code and response body for debugging
                error_detail = f"HTTP {resp.status_code}: {resp.text}"
                return False, resp.status_code, error_detail
            
        except requests.exceptions.RequestException as e:
            error_detail = f"Request Exception: {str(e)}"
            return False, 500, error_detail

    @app.route("/proxy", methods=["GET", "POST"])
    def proxy_request():
        """
        Receives username/password from requester, forwards to Ragnar, stores session cookie,
        and returns Ragnar API response JSON to requester.
        """

        # Extract username/password from Basic Auth Header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        if not auth_header.startswith("Basic "):
            return jsonify({"error": "Invalid Authorization scheme"}), 401

        try:
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
        except Exception:
            return jsonify({"error": "Invalid credentials format"}), 401
        
        # Check RAGNAR_AUTH_CHECK_ENDPOINT to see if already authenticated
        if not is_authenticated():
            # If not, forward credentials to RAGNAR_LOGIN_ENDPOINT and cache cookie
            success, status_code, error_detail = authenticate_ragnar(username, password)
            if not success:
                app.logger.error(f"Login failed: {error_detail}")
                return jsonify({"error": "Ragnar login failed", "details": error_detail}), status_code

        # Send GET request to RAGNAR_DATA_ENDPOINT using session cookie to authenticate
        try:
            resp = ragnar_session.get(f"{app.config['RAGNAR_BASE_URL']}/api/status")
            resp.raise_for_status()
            return jsonify(resp.json()), resp.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": "Failed to fetch data from Ragnar", "details": str(e)}), 502

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config['LISTEN_ADDRESS'],
        port=app.config['LISTEN_PORT'],
        threaded=False
    )
