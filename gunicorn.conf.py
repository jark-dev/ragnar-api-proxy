import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Extract bind settings
LISTEN_ADDRESS = os.getenv("LISTEN_ADDRESS", "127.0.0.1")
LISTEN_PORT = os.getenv("LISTEN_PORT", "5000")

# Gunicorn configuration variables
bind = f"{LISTEN_ADDRESS}:{LISTEN_PORT}"
workers = 1
threads = 2
timeout = 30
