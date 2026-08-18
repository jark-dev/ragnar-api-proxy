import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

load_dotenv()

# Define environment variables
LISTEN_ADDRESS = os.getenv("LISTEN_ADDRESS", "127.0.0.1")
LISTEN_PORT = os.getenv("LISTEN_PORT", "8080")
RAGNAR_URL = os.environ["RAGNAR_URL"]

# Define Ragnar API endpoints 
RAGNAR_AUTH_CHECK_ENDPOINT = "/api/auth/status"
RAGNAR_LOGIN_ENDPOINT = "/api/auth/login"
RAGNAR_DATA_ENDPOINT = "/api/status"