from dotenv import load_dotenv
import os

environment = os.getenv("ENVIRONMENT", "local")
env_file = f".env.{environment}"

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
AES_KEY = os.getenv("AES_KEY")
