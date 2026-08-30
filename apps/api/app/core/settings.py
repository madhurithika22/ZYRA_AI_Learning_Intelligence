import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from apps/api directory or parent
api_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=api_env_path)
load_dotenv()

raw_url = os.getenv("DATABASE_URL")
if not raw_url:
    raise RuntimeError("DATABASE_URL environment variable is not configured.")

DATABASE_URL: str = raw_url
