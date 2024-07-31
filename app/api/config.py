import os
from pathlib import Path

from dotenv import load_dotenv

dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path)
BASE_DIR = Path(__file__).resolve().parent


class Settings:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")


settings = Settings()