import os
from datetime import datetime, time
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

_admin_chat_id = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(_admin_chat_id) if _admin_chat_id else None

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _parse_time(value, default):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return default


WORK_START = _parse_time(os.getenv("WORK_START", "07:30"), time(7, 30))
WORK_END = _parse_time(os.getenv("WORK_END", "23:00"), time(23, 0))

WIFI_LOGIN = os.getenv("WIFI_LOGIN", "").strip()
WIFI_PASSWORD = os.getenv("WIFI_PASSWORD", "").strip()

MENU_FILE = BASE_DIR / "data" / "menu.json"
DB_FILE = BASE_DIR / "data" / "coffee_shop.db"
