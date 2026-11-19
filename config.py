import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

_admin_chat_id = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(_admin_chat_id) if _admin_chat_id else None

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

MENU_FILE = BASE_DIR / "data" / "menu.json"
CART_FILE = BASE_DIR / "cart_data.json"
