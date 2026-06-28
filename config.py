import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "eazychat")

DAILY_VIEW_LIMIT = int(os.getenv("DAILY_VIEW_LIMIT", "15"))
DAILY_LIKE_LIMIT = int(os.getenv("DAILY_LIKE_LIMIT", "10"))
DIRECT_MESSAGE_COST = int(os.getenv("DIRECT_MESSAGE_COST", "2"))
