"""Application configuration – loaded from .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


class DBConfig:
    """Neon PostgreSQL connection parameters."""
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", "5432"))
    NAME = os.getenv("DB_NAME", "neondb")
    USER = os.getenv("DB_USER", "")
    PASSWORD = os.getenv("DB_PASSWORD", "")
    SSLMODE = os.getenv("DB_SSLMODE", "require")

    @classmethod
    def connection_string(cls) -> str:
        return (
            f"host={cls.HOST} port={cls.PORT} dbname={cls.NAME} "
            f"user={cls.USER} password={cls.PASSWORD} sslmode={cls.SSLMODE}"
        )


# UI defaults
WINDOW_TITLE = "Energie-Monitor"
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700
DEFAULT_DAYS = 7  # default range for chart view
