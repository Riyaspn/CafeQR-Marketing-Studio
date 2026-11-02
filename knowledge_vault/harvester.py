import os
import json
import re
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path(__file__).parent.resolve()
SWIPE_VAULT_PATH = VAULT_DIR / "swipe_vault.json"
COMPETITOR_INTEL_PATH = VAULT_DIR / "competitor_intel.json"

HARVEST_SOURCES = [
    {
        "topic": "Aggregator Commission & Fee Hikes",
        "query": "Swiggy+OR+Zomato+commission+fee+hike+NRAI+restaurant",
        "angle": "Math Shock",
        "default_cut": "28%"
    },
    {
        "topic": "Legacy POS License Lock-ins",
        "query": "Petpooja+OR+POSist+POS+billing+restaurant+software+fee",
        "angle": "Sachet Price Destruction",
        "default_cut": "₹15,000 Upfront"
    },
    {
        "topic": "Direct QR & Dine-in Table Flow",
        "query": "restaurant+QR+ordering+UPI+table+billing+direct",
        "angle": "Hardware Speed Flex",
        "default_cut": "0% Commission"
    },
    {
        "topic": "Customer Data Hijacking",
        "query": "restaurant+customer+data+food+delivery+app+monopoly",
        "angle": "Customer Data Ownership",
        "default_cut": "100% Owned"
    }
]

def clean_text(raw):
    if not raw:
        return ""
    clean = re.sub(r'<.*?>', '', raw)
    return html.unescape(clean).strip()

def fetch_rss_headlines(query):
    """Fetches real-world public signals from Google News RSS."""
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    items = []
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            tree = ET.fromstring(response.read())
            for item in tree.findall(".//item")[:3]:
                title = clean_text(item.find("title").text if item.find("title") is not None else "")
                link = item.find("link").text if item.find("link") is not None else ""
                source_el = item.find("source")
                source = source_el.text if source_el is not None else "Public Signal"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                if title:
                    items.append({
                        "title": title,
                        "link": link,
                        "source": source,
                        "pub_date": pub_date
                    })
    except Exception as e:
        print(f"[Harvester] Warning: RSS query '{query}' failed: {e}")
        
    return items

def formulate_swipe_from_signal(signal, angle):
    """
    Synthesizes a high-converting swipe file entry from a raw news headline
    using Schwartz & Hormozi framing principles.
    """
    raw_title = signal.get("title", "")
    
    # Clean source suffix (e.g., " - The Economic Times")
    clean_headline = re.sub(r'\s*-\s*[^-]+$', '', raw_title).strip()
    
    if angle == "Math Shock":
        headline = "WHY PAY 28% COMMISSION ON EVERY ORDER?"
        subtext = f"Recent industry alert: '{clean_headline}'. Stop letting aggregators eat your net margin."
        receipt_math = {
            "bill": 500,
            "aggregator_cut": 140,
            "cafe_qr_cut": 0
        }
        cta = "Reply DEMO for Free 7-Day Trial"
        
    elif angle == "Sachet Price Destruction":
        headline = "STOP PAYING ₹15,000 UPFRONT FOR POS"
        subtext = f"Industry shifts: '{clean_headline}'. Switch to ₹99/month micro-sachet freedom."
        receipt_math = {
            "petpooja_upfront": 15000,
            "petpooja_yearly": 3000,
            "cafe_qr_monthly": 99
        }
        cta = "Claim Free Standees & Setup"
        
    elif angle == "Hardware Speed Flex":
        headline = "0.8-SECOND THERMAL KOTS PRINT DIRECT FROM TABLE QR"
        subtext = f"Operations news: '{clean_headline}'. Eliminate 15-minute waiter delays instantly."
        receipt_math = {
            "print_speed": "0.8s",
            "table_turnover_boost": "+35%"
        }
        cta = "Test The Sub-Second Demo"
        
    else: # Customer Data Ownership
        headline = "WHO ACTUALLY OWNS YOUR DINERS' PHONE NUMBERS?"
        subtext = f"Market reality: '{clean_headline}'. Own 100% of your diner CRM database."
        receipt_math = {
            "customer_retention": "100% Direct"
        }
        cta = "Own Your Customer Database"

    return {
        "angle": angle,
        "headline": headline,
        "subtext": subtext,
        "receipt_math": receipt_math,
        "cta": cta,
        "origin_headline": clean_headline,
        "source": signal.get("source", "Public Market Signal"),
        "harvested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def harvest_fresh_intel():
    """
    Scans public feeds, extracts competitive pain hooks,
    and enriches swipe_vault.json and competitor_intel.json.
    """
    print("=" * 60)
    print("🌾 Autonomous Knowledge Harvester: Scanning Competitor Signals...")
    print("=" * 60)

    # 1. Load existing swipe vault
    existing_swipes = []
    if SWIPE_VAULT_PATH.exists():
        try:
            with open(SWIPE_VAULT_PATH, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
                existing_swipes = vault_data.get("swipes", [])
        except Exception as e:
            print(f"[Harvester] Error reading swipe vault: {e}")

    existing_subtexts = {s.get("subtext", "").lower() for s in existing_swipes}
    new_swipes = []

    # 2. Harvest each channel
    for source in HARVEST_SOURCES:
        signals = fetch_rss_headlines(source["query"])
        print(f"📡 Query: '{source['topic']}' -> Found {len(signals)} live signals")
        for sig in signals:
            swipe = formulate_swipe_from_signal(sig, source["angle"])
            if swipe["subtext"].lower() not in existing_subtexts:
                new_swipes.append(swipe)
                existing_subtexts.add(swipe["subtext"].lower())

    # 3. Save enriched swipe vault
    if new_swipes:
        updated_swipes = existing_swipes + new_swipes
        vault_payload = {
            "vault_version": "2.0.0",
            "last_harvested": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_swipes": len(updated_swipes),
            "swipes": updated_swipes
        }
        with open(SWIPE_VAULT_PATH, "w", encoding="utf-8") as f:
            json.dump(vault_payload, f, indent=2, ensure_ascii=False)
        print(f"✅ Enriched Swipe Vault: Added {len(new_swipes)} new high-converting hooks (Total: {len(updated_swipes)})")
    else:
        print("ℹ️ Swipe Vault is already up to date with latest market signals.")

    # 4. Update competitor intel timestamp
    if COMPETITOR_INTEL_PATH.exists():
        try:
            with open(COMPETITOR_INTEL_PATH, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            c_data["last_verified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(COMPETITOR_INTEL_PATH, "w", encoding="utf-8") as f:
                json.dump(c_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Harvester] Could not update competitor intel: {e}")

    return {
        "new_swipes_count": len(new_swipes),
        "total_swipes": len(existing_swipes) + len(new_swipes),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    result = harvest_fresh_intel()
    print("Harvester Run Complete:", result)
