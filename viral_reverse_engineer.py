import os
import sys
import json
import re
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DRAFTS_DIR, ASSETS_DIR
import creative_brain
import poster_engine

SWIPE_CACHE_DIR = DRAFTS_DIR / "swipe_cache"
SWIPE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_ffmpeg_binary():
    """Finds system ffmpeg binary."""
    p = shutil.which("ffmpeg")
    if p:
        return p
    default_winget = Path(r"C:\Users\RIYAS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.EXE")
    if default_winget.exists():
        return str(default_winget)
    return "ffmpeg"

def download_media_from_url(url, output_prefix="viral_source"):
    """
    Downloads high-performing video/reel from Instagram, YouTube Shorts, Twitter, or TikTok using yt-dlp.
    Extracts video metadata, subtitles/captions if present, and audio track.
    """
    import yt_dlp

    ydl_opts = {
        'outtmpl': str(SWIPE_CACHE_DIR / f"{output_prefix}_%(id)s.%(ext)s"),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt/srt/best',
        'subtitleslangs': ['en', 'hi', 'en-orig'],
    }

    print(f"📥 [ViralEngineer] Fetching media via yt-dlp from: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id", "temp")
        downloaded_file = str(SWIPE_CACHE_DIR / f"{output_prefix}_{video_id}.mp4")
        if not os.path.exists(downloaded_file):
            # Fallback search if extension differed
            candidates = list(SWIPE_CACHE_DIR.glob(f"{output_prefix}_{video_id}.*"))
            if candidates:
                downloaded_file = str(candidates[0])

        return {
            "title": info.get("title", ""),
            "description": info.get("description", ""),
            "uploader": info.get("uploader", "Creator"),
            "duration": info.get("duration", 0),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "video_path": downloaded_file,
            "url": url
        }

def transcribe_media_audio(media_path):
    """
    Transcribes video audio using OpenAI Whisper (local fast execution).
    """
    try:
        import whisper
        print("🎙️ [ViralEngineer] Loading Whisper model (base) for transcript extraction...")
        model = whisper.load_model("base")
        result = model.transcribe(media_path, fp16=False)
        transcript = result.get("text", "").strip()
        segments = result.get("segments", [])
        print(f"✅ [ViralEngineer] Transcribed {len(transcript)} chars of speech.")
        return transcript, segments
    except Exception as e:
        print(f"⚠️ [ViralEngineer] Whisper transcription warning: {e}")
        return "", []

def extract_visual_keyframes(media_path, duration=15):
    """
    Uses FFmpeg to capture 3 key frames from the source video:
    - 0.8s: Scroll-stopping hook visual
    - Midpoint: Problem demonstration or core artifact
    - End: CTA or closing state
    """
    ffmpeg_bin = get_ffmpeg_binary()
    stem = Path(media_path).stem
    t1 = 0.8
    t2 = max(2.0, duration / 2.0)
    t3 = max(4.0, duration - 1.5)

    frames = {}
    for idx, (label, timestamp) in enumerate([("hook", t1), ("proof", t2), ("cta", t3)]):
        out_jpg = str(SWIPE_CACHE_DIR / f"{stem}_frame_{label}.jpg")
        cmd = [
            ffmpeg_bin, "-y",
            "-ss", str(timestamp),
            "-i", media_path,
            "-vframes", "1",
            "-q:v", "2",
            out_jpg
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if os.path.exists(out_jpg):
                frames[label] = out_jpg
        except Exception:
            pass

    return frames

def reverse_engineer_structure(source_info, transcript):
    """
    AI Creative Director analyzes the psychological anatomy of the source post:
    1. Hook Formula
    2. Core Friction Point
    3. Structural Arc (Hook -> Agitation -> Mechanism -> Call to Action)
    4. Visual Archetype (Thermal Receipt, Comparison Matrix, WhatsApp Dialogue, or Step Flow)
    """
    prompt = f"""
Act as a world-class Direct-Response Creative Director & Behavioral Psychologist.
Analyze this high-performing social video/reel to reverse-engineer its viral conversion anatomy.

SOURCE INTEL:
Title: "{source_info.get('title')}"
Uploader: "{source_info.get('uploader')}"
Description: "{source_info.get('description', '')[:300]}"
Full Voiceover Transcript:
"{transcript if transcript else source_info.get('title')}"

Deconstruct its psychological structure in strict JSON format:
{{
  "hook_formula": "The exact hook pattern (e.g. Negative Shock Question, Secret Exposé, Math Disparity, Counter-Intuitive Truth)",
  "hook_words_pattern": "First 5-8 words that arrested attention",
  "emotional_trigger": "Anger at financial loss | Fear of operational failure | Relief from speed | Disgust with legacy traps",
  "narrative_arc": "Brief 1-sentence breakdown of how it transitions from problem to mechanism",
  "recommended_visual_archetype": "Forensic Thermal Receipt | 2-Column Split Matrix | WhatsApp Digital Job Card | 3-Step Speed Flow",
  "core_lesson_for_cafeqr": "How Cafe QR should adopt this exact pacing and hook for Indian merchants"
}}
Return ONLY valid JSON.
"""
    messages = [
        {"role": "system", "content": "You are a master direct-response advertising strategist. Output strictly valid JSON."},
        {"role": "user", "content": prompt}
    ]

    try:
        raw = creative_brain.call_nvidia_nim(messages, temperature=0.15, max_tokens=600, timeout=25)
        parsed = creative_brain.clean_json_response(raw)
        return parsed
    except Exception as e:
        print(f"[ViralEngineer] Analysis fallback: {e}")
        return {
            "hook_formula": "Financial Contrast Shock",
            "hook_words_pattern": "Stop paying 28% commission on bills",
            "emotional_trigger": "Anger at financial loss",
            "narrative_arc": "Shows immediate fee deductions and contrasts with 0% direct model",
            "recommended_visual_archetype": "Forensic Thermal Receipt",
            "core_lesson_for_cafeqr": "Lead with exact rupee loss in first 3 words"
        }

def remaster_for_cafe_qr(source_info, reverse_intel, target_vertical="Restaurants & Cafes"):
    """
    Synthesizes a high-converting Cafe QR campaign adopting the reverse-engineered hook structure
    and generates a tailored 1080x1350 static poster.
    """
    headline_prompt = f"""
Act as David Ogilvy and Eugene Schwartz for Cafe QR (www.cafeqr.in).
We are remastering a viral post that used this winning hook pattern:
HOOK FORMULA: {reverse_intel.get('hook_formula')}
WINNING CADENCE: "{reverse_intel.get('hook_words_pattern')}"
RECOMMENDED ARCHETYPE: {reverse_intel.get('recommended_visual_archetype')}
TARGET VERTICAL: {target_vertical}

CRITICAL BRAND & PRICING RULES:
- Brand: strictly "Cafe QR"
- Year 1 Base Plan: ₹2,498 (Setup included)
- Year 2+ Renewal: strictly ₹999/year forever (three nines: ₹999, NEVER 9999).
- Direct delivery: 0% Commission Direct UPI | Hardware speed: 0.8s Thermal Print.
- DOMAIN RELEVANCE: Tailor all points strictly to {target_vertical}. If {target_vertical} is Car Wash / Auto Care, the friction is lost paper tokens, wet job cards, and phone call interruptions (NEVER mention restaurant POS or Petpooja). If Bakery, the friction is expired batches.

Output strict JSON:
{{
  "target_vertical": "{target_vertical}",
  "recommended_visual_archetype": "{reverse_intel.get('recommended_visual_archetype')}",
  "headline": "Bold punchy headline in ALL CAPS, max 7 words with news or specific numbers matching the viral hook pattern",
  "subtext": "Sharp 1-line sub-hook highlighting the merchant pain point with exact numbers",
  "badge": "Short badge tag (e.g. 🚨 F&B PROFIT ALERT, 🥐 BAKERY RUSH ALERT, 🚗 CAR WASH DETECTIVE, or ⚡ HARDWARE FLEX)",
  "script": "A 15-20 second conversational voiceover script adopting the same rhythm as the viral video. Ends with 'Reply DEMO for 2-minute unedited video audit'.",
  "caption": "Full Instagram/Facebook caption following Ogilvy's Informative Caption Law with hook, bullet points, transparent pricing (Year 1 ₹2,498 / Year 2+ ₹999/yr forever), and hashtags",
  "comparison": {{
    "them_label": "The specific manual flaw or legacy trap for {target_vertical} (e.g. Lost Paper Job Cards, 28% Aggregator Commission, or Bloated Software)",
    "them_points": [
      "Exact flaw 1 tailored to {target_vertical}",
      "Exact bottleneck 2 tailored to {target_vertical}",
      "Operational friction 3 tailored to {target_vertical}"
    ],
    "us_label": "Cafe QR Direct Solution",
    "us_points": [
      "Point 1 with 0% commission or Year 1 ₹2,498 / Renewal ₹999/yr forever",
      "Point 2 with sub-second thermal print or WhatsApp digital tracking",
      "Point 3 with direct UPI settlement & customer CRM"
    ]
  }},
  "cta": "Reply DEMO for 2-Minute Video Audit"
}}
Return ONLY valid JSON.
"""
    messages = [
        {"role": "system", "content": "You are a master direct-response copywriter. Output strictly valid JSON."},
        {"role": "user", "content": headline_prompt}
    ]

    raw_campaign = creative_brain.call_nvidia_nim(messages, temperature=0.2, max_tokens=1100, timeout=30)
    campaign = creative_brain.clean_json_response(raw_campaign)
    campaign["source_url"] = source_info.get("url")
    campaign["reverse_intel"] = reverse_intel
    campaign["target_vertical"] = target_vertical
    campaign["recommended_visual_archetype"] = reverse_intel.get("recommended_visual_archetype")

    # Synthesize Bespoke Poster HTML
    topic_item = {
        "title": campaign.get("headline"),
        "vertical": target_vertical,
        "deep_intel": {
            "rupee_figures": "₹2,498 Year 1 vs Legacy",
            "merchant_pain": campaign.get("subtext"),
            "awareness_stage": "Problem-Aware",
            "recommended_angle": reverse_intel.get("hook_formula"),
            "recommended_visual_archetype": reverse_intel.get("recommended_visual_archetype")
        }
    }
    campaign["poster_html"] = creative_brain.generate_poster_html(campaign, topic_item)

    # Render Poster PNG
    poster_filename = f"remastered_{re.sub(r'[^a-zA-Z0-9]', '_', target_vertical).lower()[:20]}.png"
    poster_path = poster_engine.render_poster(campaign, filename=poster_filename)
    campaign["poster_path"] = poster_path
    campaign["poster_url"] = f"/drafts/{poster_filename}"

    return campaign

def reverse_engineer_and_remaster(url, target_vertical="Restaurants & Cafes"):
    """
    End-to-End Orchestrator:
    1. Downloads URL via yt-dlp
    2. Transcribes via Whisper
    3. Extracts Keyframes via FFmpeg
    4. Reverse-engineers viral hook and pacing
    5. Remasters and renders a bespoke Cafe QR poster
    """
    print(f"\n🚀 [ViralEngineer] Initiating Reverse-Engineering for: {url}")
    source_info = download_media_from_url(url)
    
    transcript, segments = transcribe_media_audio(source_info["video_path"])
    source_info["transcript"] = transcript

    frames = extract_visual_keyframes(source_info["video_path"], source_info.get("duration", 15))
    source_info["frames"] = frames

    print(f"🧠 [ViralEngineer] Reverse-engineering viral psychological anatomy...")
    reverse_intel = reverse_engineer_structure(source_info, transcript)
    print(f"🎯 Hook Formula Identified: {reverse_intel.get('hook_formula')}")
    print(f"⚡ Recommended Archetype: {reverse_intel.get('recommended_visual_archetype')}")

    print(f"🎨 [ViralEngineer] Remastering into bespoke Cafe QR poster for {target_vertical}...")
    final_campaign = remaster_for_cafe_qr(source_info, reverse_intel, target_vertical)
    print(f"✅ [ViralEngineer] Remaster complete! Poster saved at: {final_campaign['poster_path']}")

    return final_campaign
