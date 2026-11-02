import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
DRAFTS_DIR = BASE_DIR / "drafts"
WEB_DIR = BASE_DIR / "web"

# Ensure runtime directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

# Load Environment Variables (.env)
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

# Meta Graph API Credentials
META_ACCESS_TOKEN = os.getenv("META_ADS_ACCESS_TOKEN", "") or os.getenv("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "act_2145604952429179")
META_APP_ID = os.getenv("META_APP_ID", "2416033692232877")
CAFE_QR_PAGE_ID = os.getenv("CAFE_QR_PAGE_ID", "869472002909292")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

# Google Gemini API Key (Optional free tier key; engine includes deterministic fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Cafe QR Brand Positioning
BRAND_NAME = "Cafe QR 2.0"
BRAND_URL = "https://cafeqr.in"
WHATSAPP_DEMO_PHONE = os.getenv("WHATSAPP_DEMO_PHONE", "919400000000")
WHATSAPP_DEMO_LINK = f"https://wa.me/{WHATSAPP_DEMO_PHONE}?text=Hi%20Cafe%20QR,%20I%20want%20a%20free%20live%20demo%20for%20my%20restaurant."

# Brand Design Tokens
COLOR_PRIMARY = "#FF7A00"      # Hospitality Orange
COLOR_BG_DARK = "#0B0F19"      # Deep Space Navy
COLOR_CARD_BG = "#151C2C"      # Glassmorphic Card
COLOR_ACCENT_GREEN = "#10B981" # Emerald Green (0% commission, instant profit)
COLOR_ACCENT_RED = "#EF4444"   # Red (Monopoly 28% cuts, bloated POS fees)
COLOR_TEXT_MAIN = "#F8FAFC"    # Pure crisp white
COLOR_TEXT_MUTED = "#94A3B8"   # Slate 400
