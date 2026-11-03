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

# Google Gemini API Key (Optional)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# NVIDIA NIM API (Active High-Speed Models)
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_PRIMARY = "poolside/laguna-xs-2.1"
MODEL_FALLBACK = "nvidia/nemotron-3.5-bolt-e4b"

# Cafe QR Brand Positioning & Official Channels
BRAND_NAME = "Cafe QR"
BRAND_URL = "https://www.cafeqr.in"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.cafeqr.app&hl=en_IN"
INSTAGRAM_URL = "https://www.instagram.com/cafe_qr_?igsh=MTd5azRiNmM4bDU0aw%3D%3D&utm_source=qr"
WHATSAPP_DEMO_PHONE = os.getenv("WHATSAPP_DEMO_PHONE", "919400000000")
WHATSAPP_DEMO_LINK = f"https://wa.me/{WHATSAPP_DEMO_PHONE}?text=Hi%20Cafe%20QR,%20I%20want%20a%20free%20live%20demo%20for%20my%20business."

# Supported Multi-Vertical Domains
SUPPORTED_VERTICALS = [
    "Restaurants & Cafes (Table QR, Thermal KOT, 0% Commission Direct Delivery)",
    "Bakeries & Confectioneries (Batch Production, Fresh Expiry & Barcode Billing)",
    "Car Washes & Auto Care (Job Cards, Service Tokens & WhatsApp Status Updates)",
    "Boutiques & Retail Stores (Barcode Scanning, Inventory Tags & Udhaar Tabs)",
    "Salons & Spas (Service Appointments, Stylist Commissions & Client CRM)",
    "Cloud Kitchens & Takeaway QSRs (Order Aggregation, Instant Thermal Print & UPI)"
]

# Official Transparent "Pay-Only-For-What-You-Need" Pricing (in ₹)
PRICING_BASE_YEAR_1 = 2498        # ₹999 Annual Sub + ₹1,499 Setup & Onboarding
PRICING_BASE_RENEWAL = 999        # Under ₹1,000/yr renewal (₹999/year forever)
PRICING_BOLT_ON_KOT = 499         # Kitchen Order Ticket (KOT): ₹499/year
PRICING_BOLT_ON_UDHAAR = 499      # Credit Ledger (Udhaar) Tabs: ₹499/year
PRICING_BOLT_ON_CRM = 999         # Customer CRM & Loyalty: ₹999/year
PRICING_BOLT_ON_INVENTORY = 1999  # Inventory, Purchase & Stock ERP: ₹1,999/year
PRICING_BOLT_ON_BARCODE = 999     # Barcode Scanning & Label Printing: ₹999/year
PRICING_BOLT_ON_HR_PAYROLL = 1999 # HR & Staff Payroll Management: ₹1,999/year

# Brand Design Tokens
COLOR_PRIMARY = "#FF7A00"      # Hospitality Orange
COLOR_BG_DARK = "#0B0F19"      # Deep Space Navy
COLOR_CARD_BG = "#151C2C"      # Glassmorphic Card
COLOR_ACCENT_GREEN = "#10B981" # Emerald Green (0% commission, instant profit)
COLOR_ACCENT_RED = "#EF4444"   # Red (Monopoly 28% cuts, bloated POS fees)
COLOR_TEXT_MAIN = "#F8FAFC"    # Pure crisp white
COLOR_TEXT_MUTED = "#94A3B8"   # Slate 400
