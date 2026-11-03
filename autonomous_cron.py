import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DRAFTS_DIR, BASE_DIR
import trend_radar
import creative_brain
import poster_engine
import telegram_notifier

VAULT_DIR = BASE_DIR / "knowledge_vault"
VAULT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_FILE = VAULT_DIR / "processed_stories.json"
DRAFTS_INDEX = DRAFTS_DIR / "saved_drafts.json"

def load_processed_titles():
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_title(title):
    processed = load_processed_titles()
    processed.add(title.strip().lower())
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, indent=2)

def save_campaign_draft(campaign):
    drafts = []
    if DRAFTS_INDEX.exists():
        try:
            with open(DRAFTS_INDEX, "r", encoding="utf-8") as f:
                drafts = json.load(f)
        except Exception:
            drafts = []

    # Insert at top
    campaign["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    drafts.insert(0, campaign)
    drafts = drafts[:50]  # keep latest 50 drafts

    with open(DRAFTS_INDEX, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)

def run_autonomous_poster_cycle():
    """
    Executes one complete autonomous cycle:
    1. Scans 26 multi-vertical streams for breaking Indian merchant news
    2. Filters out previously processed stories
    3. Synthesizes a high-converting campaign adhering to the 4 Masters & 5 Formats
    4. Renders a 1080x1350 PNG with Cafe QR logo & verified pricing
    5. Dispatches an instant Telegram alert for review & 1-click publishing
    """
    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Starting Autonomous Poster Generation Cycle...")
    trends = trend_radar.fetch_trending_topics(limit=15)
    if not trends:
        print("ℹ️ No trends returned from streams.")
        return {"status": "NO_TRENDS"}

    processed_titles = load_processed_titles()
    fresh_candidate = None

    for t in trends:
        norm_title = t.get("title", "").strip().lower()
        if norm_title not in processed_titles:
            fresh_candidate = t
            break

    if not fresh_candidate:
        print("ℹ️ All trending stories have already been processed into drafts. Standing by.")
        return {"status": "ALREADY_UP_TO_DATE"}

    print(f"🎯 Selected Fresh Story: \"{fresh_candidate.get('title')}\"")
    print(f"🏷️ Vertical: {fresh_candidate.get('vertical', 'Multi-Vertical')}")

    # 1. Generate Campaign with 4 Masters & Awareness Alignment
    campaign = creative_brain.generate_creative_campaign(fresh_candidate)

    # 2. Render High-Res Poster PNG
    poster_filename = f"auto_{int(time.time())}_{campaign.get('target_vertical', 'post').lower()[:12].replace(' ', '_')}.png"
    poster_path = poster_engine.render_poster(campaign, filename=poster_filename)
    campaign["poster_path"] = poster_path
    campaign["poster_url"] = f"/drafts/{poster_filename}"

    # 3. Save to Studio Drafts Gallery
    save_campaign_draft(campaign)
    save_processed_title(fresh_candidate.get("title"))

    # 4. Dispatch Telegram Review Alert
    tg_result = telegram_notifier.send_telegram_poster_alert(campaign, poster_path)
    campaign["telegram_alert"] = tg_result

    print(f"✅ Autonomous Cycle Complete! Poster saved: {poster_path}")
    return {
        "status": "SUCCESS",
        "title": fresh_candidate.get("title"),
        "vertical": campaign.get("target_vertical"),
        "poster_path": poster_path,
        "poster_url": campaign.get("poster_url"),
        "telegram_alert": tg_result
    }

if __name__ == "__main__":
    result = run_autonomous_poster_cycle()
    print(json.dumps(result, indent=2))

