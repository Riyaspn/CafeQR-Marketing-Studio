import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
from pathlib import Path
from config import DRAFTS_DIR, ASSETS_DIR

AUDIO_CACHE_DIR = DRAFTS_DIR / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Situation Archetypes & Dynamic Search Profiles
SITUATION_CONFIGS = {
    "BREAKING_TENSION": {
        "title": "Dramatic Tension & News Expose",
        "genre": "Suspense / High Stakes",
        "search_terms": ["ambient synthesizer", "dramatic ambient", "dark synthesizer"],
        "cache_filename": "bgm_breaking_tension.ogg",
        "trending_ig_tip": "Else — Paris (Popular for exposés & fee hike reactions)"
    },
    "TECH_SPEED_FLEX": {
        "title": "Kinetic Electronic Tempo",
        "genre": "High Velocity / Hardware Flex",
        "search_terms": ["synthesizer demo", "electronic techno loop", "future bass"],
        "cache_filename": "bgm_tech_speed_flex.ogg",
        "trending_ig_tip": "Interworld — Metamorphosis (High-energy speed flex)"
    },
    "PRICE_DISRUPTION": {
        "title": "Future Bass & Punchy Disruptor",
        "genre": "Bold Disruption / Sachet Fight",
        "search_terms": ["electronic beat", "synth bass loop", "dynamic electronic rhythm"],
        "cache_filename": "bgm_price_disruption.ogg",
        "trending_ig_tip": "AP Dhillon — Dil Nu Instrumental (Punchy bass beat)"
    },
    "CAFE_AMBIANCE": {
        "title": "Warm Acoustic & Chill Cafe Lounge",
        "genre": "Acoustic / Customer Experience",
        "search_terms": ["acoustic piano", "chillout guitar", "ambient piano lounge"],
        "cache_filename": "bgm_cafe_ambiance.ogg",
        "trending_ig_tip": "Lofi Fruits Music — Coffee & Chill (Smooth coffeehouse vibe)"
    }
}

DEFAULT_SITUATION = "BREAKING_TENSION"

def _search_wikimedia_audio(query):
    """
    Dynamically searches Wikimedia Commons Open Audio API for commercial-safe,
    CC0/Creative Commons audio files matching the query and returns the live CDN URL.
    """
    ctx = ssl._create_unverified_context()
    encoded_query = urllib.parse.quote(f"{query} filetype:audio")
    api_url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        f"&gsrnamespace=6&gsrsearch={encoded_query}&gsrlimit=4&prop=imageinfo"
        f"&iiprop=url|mime|size&format=json"
    )
    headers = {
        "User-Agent": "CafeQRMarketingStudio/2.0 (https://cafeqr.in; contact@cafeqr.in) Python/urllib"
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                imageinfo = page.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    file_url = info.get("url")
                    mime = info.get("mime", "")
                    # Filter for audio MIME types
                    if file_url and ("audio" in mime or file_url.endswith((".ogg", ".wav", ".mp3", ".oga"))):
                        return file_url, page.get("title", "Online Audio Track")
    except Exception as e:
        print(f"[MusicFetcher] Wikimedia search error for '{query}': {e}")
    return None, None

def get_track_for_situation(situation_key):
    """
    Downloads or retrieves from cache the optimal commercial-safe royalty-free
    background music track matching the AI campaign's situation.
    """
    key = situation_key if situation_key in SITUATION_CONFIGS else DEFAULT_SITUATION
    config = SITUATION_CONFIGS[key]
    cached_path = AUDIO_CACHE_DIR / config["cache_filename"]

    # 1. Check if cached and valid (>10KB)
    if cached_path.exists() and cached_path.stat().st_size > 10000:
        return str(cached_path)

    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "CafeQRMarketingStudio/2.0 (https://cafeqr.in; contact@cafeqr.in) Python/urllib"
    }

    # 2. Dynamic Live Online Search via Wikimedia Commons Open Audio API
    search_queries = config.get("search_terms", ["synthesizer demo"])
    for query in search_queries:
        print(f"[MusicFetcher] Searching online audio catalog for '{query}'...")
        file_url, track_title = _search_wikimedia_audio(query)
        if file_url:
            try:
                print(f"[MusicFetcher] Found track '{track_title}'. Downloading: {file_url}...")
                req = urllib.request.Request(file_url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=25) as response:
                    content = response.read()
                    if len(content) > 10000:
                        with open(cached_path, "wb") as f:
                            f.write(content)
                        print(f"✅ Successfully cached dynamic music: {cached_path.name} ({len(content):,} bytes)")
                        return str(cached_path)
            except Exception as dl_err:
                print(f"[MusicFetcher] Download failed from {file_url}: {dl_err}")
                continue

    # 3. Fallback: Check if any other audio file exists in the cache
    for f in AUDIO_CACHE_DIR.glob("*.*"):
        if f.suffix in [".ogg", ".mp3", ".wav", ".oga"] and f.stat().st_size > 10000:
            print(f"[MusicFetcher] Using existing cached audio fallback: {f.name}")
            return str(f)

    return None

def get_audio_info(situation_key):
    """Returns metadata about the situation's music and trending audio recommendation."""
    key = situation_key if situation_key in SITUATION_CONFIGS else DEFAULT_SITUATION
    return SITUATION_CONFIGS[key]

if __name__ == "__main__":
    for k in SITUATION_CONFIGS.keys():
        print(f"\n--- Testing situation: {k} ---")
        p = get_track_for_situation(k)
        print(f"Result for {k} -> {p}")
