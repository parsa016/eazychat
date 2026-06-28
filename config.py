import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
VERIFICATION_GROUP_ID = int(os.getenv("VERIFICATION_GROUP_ID", "0"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "eazychat")

DAILY_VIEW_LIMIT = int(os.getenv("DAILY_VIEW_LIMIT", "15"))
DAILY_LIKE_LIMIT = int(os.getenv("DAILY_LIKE_LIMIT", "10"))
DIRECT_MESSAGE_COST = int(os.getenv("DIRECT_MESSAGE_COST", "2"))
CHAT_REQUEST_COST = int(os.getenv("CHAT_REQUEST_COST", "2"))
LIKE_WITH_DIRECT_COST = int(os.getenv("LIKE_WITH_DIRECT_COST", "2"))

SIGNUP_BONUS = int(os.getenv("SIGNUP_BONUS", "2"))
PROFILE_COMPLETE_BONUS = int(os.getenv("PROFILE_COMPLETE_BONUS", "8"))
REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "10"))
REFERRAL_PURCHASE_PERCENT = int(os.getenv("REFERRAL_PURCHASE_PERCENT", "10"))

# Proxy settings (for Iran/filtered networks)
PROXY_URL = os.getenv("PROXY_URL", "")
