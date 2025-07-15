"""Configuration settings for the application."""

import os
from dotenv import load_dotenv
from web3 import Web3

environment = os.getenv("ENVIRONMENT", "local")
ENV_FILE = f".env.{environment}"

if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")
AES_KEY = os.getenv("AES_KEY")
if not AES_KEY:
    raise ValueError("AES_KEY is not set in the environment variables.")
PROVIDER_URL = os.getenv("PROVIDER_URL")

def get_web3_provider():
    """Get a Web3 provider for the Sepolia testnet."""
    if not PROVIDER_URL:
        raise ValueError("PROVIDER_URL is not set in the environment variables.")
    return Web3(Web3.HTTPProvider(PROVIDER_URL))
