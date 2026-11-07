import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import threading

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

_CYCLE_LOCK = threading.Lock()

def load_processed_history():
    """
    Loads comprehensive history of processed titles, categories, and generated headlines.
    Handles legacy list-of-strings format transparently.
    """
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Legacy format: list of raw titles
                    return {
                        "titles": set(t.strip().lower() for t in data if isinstance(t, str)),
                        "headlines": set(),
                        "categories": {},
                        "records": [{"title": t, "timestamp": 0} for t in data if isinstance(t, str)]
                    }
                elif isinstance(data, dict):
                    return {
                        "titles": set(t.strip().lower() for t in data.get("titles", []) if isinstance(t, str)),
                        "headlines": set(h.strip().upper() for h in data.get("headlines", []) if isinstance(h, str)),
                        "categories": data.get("categories", {}),
                        "records": data.get("records", [])
                    }
        except Exception as e:
            print(f"⚠️ [AutonomousCron] Error reading processed history: {e}")
    return {
        "titles": set(),
        "headlines": set(),
        "categories": {},
        "records": []
    }

def record_processed_story(title=None, category=None, vertical=None, headline=None):
    """
    Records an article title, category, vertical, and generated headline with timestamp.
    """
    history = load_processed_history()
    now_ts = int(time.time())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if title:
        history["titles"].add(title.strip().lower())
    if headline:
        history["headlines"].add(headline.strip().upper())
    if category:
        history["categories"][category] = now_ts

    record = {
        "title": title,
        "category": category,
        "vertical": vertical,
        "headline": headline,
        "timestamp": now_ts,
        "created_at": now_str
    }
    history["records"].append(record)

    # Retain last 60 records
    if len(history["records"]) > 60:
        history["records"] = history["records"][-60:]

    payload = {
        "titles": list(history["titles"]),
        "headlines": list(history["headlines"]),
        "categories": history["categories"],
        "records": history["records"]
    }

    try:
        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        print(f"⚠️ [AutonomousCron] Error saving processed history: {e}")

def headline_similarity(h1, h2):
    """
    Computes Jaccard word-overlap similarity between two headlines.
    Ignores common grammatical stopwords to accurately catch duplicate angles.
    """
    if not h1 or not h2:
        return 0.0
    import re
    stopwords = {"THE", "OF", "AND", "A", "IN", "FOR", "YOUR", "WITH", "TO", "ON", "IS", "AT", "NOW", "ALL"}
    words1 = {w for w in re.findall(r'\b[A-Z0-9%₹]+\b', h1.upper()) if w not in stopwords}
    words2 = {w for w in re.findall(r'\b[A-Z0-9%₹]+\b', h2.upper()) if w not in stopwords}
    if not words1 or not words2:
        return 0.0
    overlap = words1.intersection(words2)
    return len(overlap) / min(len(words1), len(words2))

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

    # Auto-prune older drafts from disk to prevent disk accumulation on Render
    if len(drafts) > 5:
        for old_d in drafts[5:]:
            old_p = old_d.get("poster_path")
            if old_p and os.path.exists(old_p):
                try:
                    os.remove(old_p)
                    print(f"🗑️ [AutoPrune] Cleaned up older draft image: {old_p}")
                except Exception:
                    pass
            old_s = old_d.get("story_path")
            if old_s and os.path.exists(old_s):
                try:
                    os.remove(old_s)
                    print(f"🗑️ [AutoPrune] Cleaned up older story image: {old_s}")
                except Exception:
                    pass
        drafts = drafts[:5]

    with open(DRAFTS_INDEX, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)

def run_autonomous_poster_cycle():
    """
    Executes one complete autonomous cycle:
    1. Scans 26 multi-vertical streams for breaking Indian merchant news
    2. Multi-Tier Deduplication:
       - Discards previously processed raw article titles
       - Prioritizes fresh verticals/categories (prevents back-to-back duplicate topics)
       - Enforces strict headline diversity (blocks duplicate angles like 'KEEP 100 PERCENT OF DELIVERY REVENUE')
    3. Synthesizes a high-converting campaign adhering to the 4 Masters & 5 Formats
    4. Renders a 1080x1350 PNG with Cafe QR logo & verified pricing
    5. Generates companion 9:16 Story asset (1080x1920)
    6. Dispatches an instant Telegram alert for review & 1-click publishing
    """
    if not _CYCLE_LOCK.acquire(blocking=False):
        print("ℹ️ [AutonomousCron] Another cycle is already actively executing. Skipping redundant call.")
        return {"status": "CYCLE_ALREADY_IN_PROGRESS"}

    try:
        print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Starting Autonomous Poster Generation Cycle...")
        trends = trend_radar.fetch_trending_topics(limit=25)
        if not trends:
            print("ℹ️ No trends returned from streams.")
            return {"status": "NO_TRENDS"}

        history = load_processed_history()
        processed_titles = history.get("titles", set())
        banned_headlines = set(history.get("headlines", set()))

        # Inspect current drafts in gallery for recent verticals & headlines
        recent_draft_categories = set()
        recent_draft_verticals = []
        if DRAFTS_INDEX.exists():
            try:
                with open(DRAFTS_INDEX, "r", encoding="utf-8") as f:
                    drafts = json.load(f)
                    for d in drafts:
                        if d.get("headline"):
                            banned_headlines.add(d.get("headline").strip().upper())
                        if d.get("category"):
                            recent_draft_categories.add(d.get("category"))
                        if d.get("target_vertical"):
                            recent_draft_verticals.append(d.get("target_vertical"))
            except Exception:
                pass

        # Cooldown window for categories: 20 hours
        now_ts = int(time.time())
        CATEGORY_COOLDOWN_SECONDS = 20 * 3600
        category_timestamps = history.get("categories", {})

        # Partition un-processed trends into 3 priority tiers
        tier1_candidates = []  # Fresh title, fresh category, fresh vertical
        tier2_candidates = []  # Fresh title, fresh category
        tier3_candidates = []  # Fresh title, but category in cooldown

        last_vertical = recent_draft_verticals[0] if recent_draft_verticals else ""

        for t in trends:
            raw_title = t.get("title", "").strip()
            norm_title = raw_title.lower()
            if norm_title in processed_titles:
                continue

            cat = t.get("category", "")
            vert = t.get("vertical", "")
            cat_last_used = category_timestamps.get(cat, 0)
            in_cooldown = (now_ts - cat_last_used) < CATEGORY_COOLDOWN_SECONDS or (cat in recent_draft_categories)
            is_same_vert = (vert == last_vertical)

            if not in_cooldown and not is_same_vert:
                tier1_candidates.append(t)
            elif not in_cooldown:
                tier2_candidates.append(t)
            else:
                tier3_candidates.append(t)

        candidate_pool = tier1_candidates or tier2_candidates or tier3_candidates
        if not candidate_pool:
            print("ℹ️ All trending stories across 26 streams have been processed. Standing by.")
            return {"status": "ALREADY_UP_TO_DATE"}

        fresh_candidate = None
        campaign = None

        # Iterate through candidates and verify generated headline diversity
        for cand in candidate_pool:
            print(f"🎯 Evaluating Candidate: \"{cand.get('title')}\" [{cand.get('vertical')}]")
            test_campaign = creative_brain.generate_creative_campaign(cand, banned_headlines=list(banned_headlines))
            cand_headline = test_campaign.get("headline", "").strip().upper()

            # Verify headline similarity against recently used headlines
            is_duplicate = False
            for prev_h in banned_headlines:
                sim = headline_similarity(cand_headline, prev_h)
                if sim > 0.60:
                    print(f"⚠️ Headline \"{cand_headline}\" is too similar ({sim:.2f}) to recent \"{prev_h}\". Trying next story...")
                    is_duplicate = True
                    break

            if not is_duplicate:
                fresh_candidate = cand
                campaign = test_campaign
                break

        # Fallback to first candidate if all candidates triggered near-similarity
        if not fresh_candidate:
            fresh_candidate = candidate_pool[0]
            campaign = creative_brain.generate_creative_campaign(fresh_candidate, banned_headlines=list(banned_headlines))

        print(f"✅ Selected Fresh Story: \"{fresh_candidate.get('title')}\"")
        print(f"🏷️ Vertical: {campaign.get('target_vertical', fresh_candidate.get('vertical', 'Multi-Vertical'))}")
        print(f"📢 Headline: \"{campaign.get('headline')}\"")

        # 2. Render High-Res Poster PNG (and automatic 9:16 Story asset)
        poster_filename = f"auto_{int(time.time())}_{campaign.get('target_vertical', 'post').lower()[:12].replace(' ', '_')}.png"
        poster_path = poster_engine.render_poster(campaign, filename=poster_filename)
        campaign["poster_path"] = poster_path
        campaign["poster_file"] = poster_path
        campaign["poster_url"] = f"/drafts/{poster_filename}"
        campaign["category"] = fresh_candidate.get("category", "")

        story_filename = f"story_{poster_filename}"
        story_path = DRAFTS_DIR / story_filename
        if story_path.exists():
            campaign["story_path"] = str(story_path)
            campaign["story_file"] = str(story_path)
            campaign["story_url"] = f"/drafts/{story_filename}"

        # 3. Save to Studio Drafts Gallery & Record to Processed History
        save_campaign_draft(campaign)
        record_processed_story(
            title=fresh_candidate.get("title"),
            category=fresh_candidate.get("category"),
            vertical=campaign.get("target_vertical"),
            headline=campaign.get("headline")
        )

        # 4. Dispatch Telegram Review Alert
        tg_result = telegram_notifier.send_telegram_poster_alert(campaign, poster_path)
        campaign["telegram_alert"] = tg_result

        print(f"✅ Autonomous Cycle Complete! Poster saved: {poster_path}")
        return {
            "status": "SUCCESS",
            "title": fresh_candidate.get("title"),
            "vertical": campaign.get("target_vertical"),
            "headline": campaign.get("headline"),
            "poster_path": poster_path,
            "poster_url": campaign.get("poster_url"),
            "telegram_alert": tg_result
        }
    finally:
        _CYCLE_LOCK.release()

if __name__ == "__main__":
    result = run_autonomous_poster_cycle()
    print(json.dumps(result, indent=2))

