import os
import uuid
import json
import time
import asyncio
import subprocess
import base64
from pathlib import Path
import imageio_ffmpeg
import edge_tts
from playwright.sync_api import sync_playwright
from config import BASE_DIR, DRAFTS_DIR, ASSETS_DIR
import music_fetcher

def _get_b64_asset(filename, mime="image/png"):
    p = ASSETS_DIR / filename
    if p.exists():
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            mime = "image/jpeg"
        elif filename.endswith(".svg"):
            mime = "image/svg+xml"
        with open(p, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    return ""

# Voice Options
VOICES = {
    "prabhat": "en-IN-PrabhatNeural",  # Energetic Indian Male
    "neerja": "en-IN-NeerjaNeural",    # Clear Indian Female
    "christopher": "en-US-ChristopherNeural"  # Viral Tech Male
}

async def synthesize_voiceover(script_text, output_mp3_path, voice_key="prabhat"):
    """
    Synthesizes script into crystal clear neural voiceover using edge-tts (100% free).
    """
    voice = VOICES.get(voice_key, VOICES["prabhat"])
    communicate = edge_tts.Communicate(script_text, voice, rate="+5%")
    await communicate.save(str(output_mp3_path))
    return str(output_mp3_path)

def render_reel_frame(headline, subtext, badge_text, step_text, output_png_path, cta_text="REPLY 'DEMO' FOR 2-MIN VIDEO AUDIT", proof_sub="Diner scans Table QR &rarr; Instant thermal print &rarr; 0% Commission"):
    """
    Renders an agency-grade 1080x1920 vertical Reel slide with real cafe atmosphere,
    real Cafe QR brand logo, and real hardware mockups.
    """
    logo_b64 = _get_b64_asset("logo.png")
    printer_b64 = _get_b64_asset("printer-3inch.png")
    bg_b64 = _get_b64_asset("cafe_warm_high_end_interior_1769345033566.png")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{
    width: 1080px;
    height: 1920px;
    background: #080C14;
    color: white;
    font-family: 'Plus Jakarta Sans', sans-serif;
    padding: 100px 70px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
  }}

  /* Real Cafe Photo Atmosphere */
  .bg-photo {{
    position: absolute;
    inset: 0;
    background-image: url('{bg_b64}');
    background-size: cover;
    background-position: center;
    filter: brightness(0.24) contrast(1.15);
    z-index: 0;
  }}

  .vignette {{
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 40%, rgba(11, 15, 25, 0.4) 0%, rgba(8, 12, 20, 0.95) 90%);
    z-index: 1;
  }}

  .glow-orb {{
    position: absolute;
    width: 700px;
    height: 700px;
    top: 25%;
    right: -150px;
    background: radial-gradient(circle, rgba(255, 122, 0, 0.25) 0%, transparent 70%);
    filter: blur(100px);
    z-index: 1;
  }}

  /* Top Bar with Real Cafe QR Logo */
  .top-bar {{
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.12);
    padding-bottom: 30px;
  }}

  .brand-pill {{
    display: flex;
    align-items: center;
    gap: 14px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    padding: 12px 24px;
    border-radius: 20px;
    backdrop-filter: blur(20px);
  }}

  .brand-logo-img {{
    height: 44px;
    width: auto;
    object-fit: contain;
  }}

  .brand-text {{
    font-family: 'Outfit', sans-serif;
    font-size: 28px;
    font-weight: 900;
  }}
  .brand-text span {{
    color: #FF7A00;
  }}

  .top-badge {{
    background: rgba(255, 122, 0, 0.2);
    border: 2px solid #FF7A00;
    color: #FF9933;
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 900;
    padding: 12px 30px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }}

  /* Center Stage */
  .center-content {{
    position: relative;
    z-index: 2;
    margin: 40px 0;
  }}

  .eyebrow {{
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: #EF4444;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 20px;
  }}

  .headline {{
    font-family: 'Outfit', sans-serif;
    font-size: 82px;
    font-weight: 900;
    line-height: 1.05;
    text-transform: uppercase;
    color: #FFFFFF;
    margin-bottom: 32px;
    letter-spacing: -2px;
  }}

  .headline span {{
    color: #FF7A00;
    text-shadow: 0 0 50px rgba(255, 122, 0, 0.5);
  }}

  .subtext {{
    font-size: 36px;
    font-weight: 600;
    color: #CBD5E1;
    line-height: 1.35;
    margin-bottom: 40px;
  }}

  /* Real Hardware / App Proof Showcase */
  .proof-card {{
    background: rgba(21, 28, 44, 0.85);
    border: 2px solid rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(25px);
    border-radius: 36px;
    padding: 40px;
    display: flex;
    align-items: center;
    gap: 32px;
    box-shadow: 0 30px 70px rgba(0, 0, 0, 0.6);
  }}

  .printer-thumb {{
    height: 170px;
    width: auto;
    object-fit: contain;
    filter: drop-shadow(0 15px 30px rgba(0,0,0,0.9));
  }}

  .proof-details {{
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}

  .proof-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 34px;
    font-weight: 900;
    color: #10B981;
  }}

  .proof-sub {{
    font-size: 24px;
    color: #E2E8F0;
    line-height: 1.35;
  }}

  /* Bottom Hormozi-Style Action Hook */
  .bottom-cta {{
    position: relative;
    z-index: 2;
    background: #FF7A00;
    color: #0B0F19;
    font-family: 'Outfit', sans-serif;
    font-size: 34px;
    font-weight: 900;
    padding: 34px 50px;
    border-radius: 30px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: -0.5px;
    box-shadow: 0 25px 60px rgba(255, 122, 0, 0.45);
  }}
</style>
</head>
<body>
  <div class="bg-photo"></div>
  <div class="vignette"></div>
  <div class="glow-orb"></div>

  <!-- Real Cafe QR Logo Header -->
  <div class="top-bar">
    <div class="brand-pill">
      <img class="brand-logo-img" src="{logo_b64}" alt="Cafe QR Logo" />
      <div class="brand-text">CAFE <span>QR 2.0</span></div>
    </div>
    <div class="top-badge">{badge_text}</div>
  </div>

  <!-- Center Stage -->
  <!-- Center Stage -->
  <div class="center-content">
    <div class="eyebrow">⚡ {badge_text}</div>
    <h1 class="headline">{headline}</h1>
    <p class="subtext">{subtext}</p>
    
    <!-- Real Hardware Proof Card -->
    <div class="proof-card">
      <img class="printer-thumb" src="{printer_b64}" alt="Cafe QR Thermal Printer" />
      <div class="proof-details">
        <div class="proof-title">0.8-SEC SUB-SECOND KOT</div>
        <div class="proof-sub">{proof_sub}</div>
      </div>
    </div>
  </div>

  <!-- Bottom CTA -->
  <div class="bottom-cta">
    {cta_text} 🚀
  </div>
</body>
</html>"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=str(output_png_path))
        browser.close()

def render_reel_video(creative_data, voice_key="prabhat", filename=None):
    """
    Renders a true broadcast-grade 9:16 vertical MP4 Reel with kinetic motion:
    1. Synthesizes neural voiceover (Edge-TTS)
    2. Transcribes with OpenAI Whisper for exact word-by-word timestamps
    3. Builds animated HTML stage with animated receipt ejection & karaoke subtitles
    4. Records true 60FPS motion video via Playwright headless Chromium
    5. Muxes with FFmpeg into high-bitrate H.264 MP4 with ducked background music
    """
    import whisper

    uid = uuid.uuid4().hex[:8]
    if not filename:
        filename = f"reel_{uid}.mp4"

    temp_dir = DRAFTS_DIR / f"temp_{uid}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    mp3_path = temp_dir / f"voice_{uid}.mp3"
    html_path = temp_dir / f"stage_{uid}.html"
    output_mp4 = DRAFTS_DIR / filename

    script_text = creative_data.get("script", "Stop giving 28% to aggregators. Switch to Cafe QR today.")
    headline = creative_data.get("headline", "RESTAURANT PROFIT ALERT")
    subtext = creative_data.get("subtext", "Stop losing 28% per order.")
    badge = creative_data.get("badge", "🚨 F&B PROFIT ALERT")
    cta = creative_data.get("cta", "Reply DEMO for 2-Minute Video Audit")

    # Step 1: Synthesize Voiceover
    print(f"🎙️ [ReelEngine] Synthesizing neural voiceover ({voice_key})...")
    asyncio.run(synthesize_voiceover(script_text, mp3_path, voice_key))

    # Step 2: Extract Word-Level Timestamps with OpenAI Whisper aligned to SCRIPT WORDS (Zero Typos)
    print(f"🧠 [ReelEngine] Extracting word-level timestamps with OpenAI Whisper...")
    model = whisper.load_model("tiny")
    whisper_res = model.transcribe(str(mp3_path), word_timestamps=True)

    # Clean script words with 100% correct spelling, preserving case
    script_words = [w.strip() for w in script_text.split() if w.strip()]
    whisper_words = []
    for segment in whisper_res.get("segments", []):
        for w in segment.get("words", []):
            whisper_words.append({
                "start": round(w.get("start", 0), 2),
                "end": round(w.get("end", 0), 2)
            })

    total_duration = whisper_res.get("segments", [{}])[-1].get("end", 15.0) + 0.6

    words_data = []
    num_words = min(len(script_words), len(whisper_words))
    for i in range(num_words):
        clean_word = script_words[i].strip(",.!?\":;'")
        words_data.append({
            "word": clean_word,
            "start": whisper_words[i]["start"],
            "end": whisper_words[i]["end"]
        })
    if len(script_words) > len(whisper_words):
        last_end = whisper_words[-1]["end"] if whisper_words else total_duration - 1.0
        step = (total_duration - last_end) / (len(script_words) - len(whisper_words) + 1)
        for i in range(len(whisper_words), len(script_words)):
            s = round(last_end + (i - len(whisper_words)) * step, 2)
            e = round(s + step * 0.9, 2)
            words_data.append({"word": script_words[i].strip(",.!?\":;'"), "start": s, "end": e})

    # Step 3: Base64 Assets
    logo_b64 = _get_b64_asset("logo.png")
    printer_b64 = _get_b64_asset("printer-3inch.png")
    bg_b64 = _get_b64_asset("cafe_warm_high_end_interior_1769345033566.png")
    pos_counter_b64 = _get_b64_asset("scene_pos_counter.jpg") or bg_b64
    table_qr_b64 = _get_b64_asset("scene_table_qr.jpg") or bg_b64

    # Scene timing marks (dynamically calculated)
    t1 = round(total_duration * 0.22, 1)  # Scene 1: The Hook (e.g. 0 to 5s)
    t2 = round(total_duration * 0.52, 1)  # Scene 2: Product Flex (e.g. 5 to 12s)
    t3 = round(total_duration * 0.78, 1)  # Scene 3: The Math Comparison (e.g. 12 to 18s)
    receipt_trigger = round(t1 + 1.5, 1)

    # Style Headline with Accent
    words = headline.split()
    if len(words) > 2:
        styled_head = " ".join(words[:-2]) + f" <span>{' '.join(words[-2:])}</span>"
    else:
        styled_head = f"<span>{headline}</span>"

    # Step 4: Build Multi-Scene Animated HTML Stage
    html_content = f"""<!DOCTYPE html>
<html style="background: #080C14;">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  html, body {{
    width: 1080px;
    height: 1920px;
    background: #080C14 !important;
    color: white;
    font-family: 'Plus Jakarta Sans', 'Outfit', 'Segoe UI', system-ui, -apple-system, sans-serif;
    position: relative;
    overflow: hidden;
  }}

  /* Top Global Header */
  .global-header {{
    position: absolute;
    top: 70px;
    left: 60px;
    right: 60px;
    z-index: 10;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .brand-pill {{
    display: flex;
    align-items: center;
    gap: 14px;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 14px 28px;
    border-radius: 22px;
    backdrop-filter: blur(20px);
  }}

  .brand-logo-img {{ height: 48px; width: auto; }}
  .brand-text {{ font-family: 'Outfit', sans-serif; font-size: 30px; font-weight: 900; }}
  .brand-text span {{ color: #FF7A00; }}

  .top-badge {{
    background: rgba(255, 122, 0, 0.25);
    border: 2px solid #FF7A00;
    color: #FF9933;
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 900;
    padding: 12px 30px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }}

  /* Multi-Scene System */
  .scene {{
    position: absolute;
    inset: 0;
    opacity: 0;
    visibility: hidden;
    transform: scale(0.97);
    transition: opacity 0.45s ease-in-out, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    padding: 190px 60px 220px 60px;
    z-index: 2;
  }}

  .scene.active {{
    opacity: 1;
    visibility: visible;
    transform: scale(1.0);
  }}

  /* Background Layers */
  .bg-layer {{
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    z-index: 0;
  }}

  .vignette {{
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 50%, rgba(8, 12, 20, 0.45) 0%, rgba(8, 12, 20, 0.95) 100%);
    z-index: 1;
  }}

  /* Scene 1: The Hook */
  .scene-hook-alert {{
    display: inline-block;
    align-self: flex-start;
    background: rgba(239, 68, 68, 0.25);
    border: 2px solid #EF4444;
    color: #F87171;
    font-family: 'Outfit', sans-serif;
    font-size: 26px;
    font-weight: 900;
    padding: 10px 26px;
    border-radius: 999px;
    margin-bottom: 24px;
    animation: alert-pulse 1.5s infinite alternate;
  }}

  @keyframes alert-pulse {{
    0% {{ transform: scale(1); box-shadow: 0 0 10px rgba(239, 68, 68, 0.3); }}
    100% {{ transform: scale(1.04); box-shadow: 0 0 30px rgba(239, 68, 68, 0.8); }}
  }}

  .scene-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 72px;
    font-weight: 900;
    line-height: 1.08;
    text-transform: uppercase;
    color: #FFFFFF;
    margin-bottom: 35px;
    letter-spacing: -1.5px;
  }}
  .scene-title span {{
    color: #FF7A00;
    text-shadow: 0 0 45px rgba(255, 122, 0, 0.6);
  }}

  /* Hook Breakdown Card */
  .breakdown-card {{
    background: rgba(15, 23, 42, 0.88);
    border: 2px solid rgba(255, 255, 255, 0.15);
    border-radius: 32px;
    padding: 36px 40px;
    backdrop-filter: blur(25px);
    display: flex;
    flex-direction: column;
    gap: 20px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.8);
  }}

  .breakdown-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 32px;
    font-weight: 700;
  }}
  .breakdown-row.danger {{ color: #EF4444; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 16px; }}
  .breakdown-row.net {{ color: #10B981; font-size: 38px; font-weight: 900; }}

  /* Scene 2: Product In Action */
  .hardware-center {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 30px;
    position: relative;
  }}

  .printer-container {{
    position: relative;
    width: 440px;
    height: 340px;
    display: flex;
    justify-content: center;
    align-items: flex-end;
  }}

  .printer-img {{
    width: 100%;
    height: auto;
    position: relative;
    z-index: 3;
    filter: drop-shadow(0 25px 45px rgba(0,0,0,0.95));
  }}

  .animated-receipt {{
    position: absolute;
    top: 40px;
    width: 300px;
    background: #FFFFFF;
    color: #111827;
    border-radius: 8px;
    padding: 18px;
    font-family: monospace;
    font-size: 15px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.5);
    z-index: 2;
    transform: translateY(80px);
    opacity: 0;
    animation: receipt-eject 1.2s cubic-bezier(0.16, 1, 0.3, 1) {receipt_trigger}s forwards;
  }}

  @keyframes receipt-eject {{
    0% {{ transform: translateY(80px); opacity: 0; }}
    20% {{ opacity: 1; }}
    100% {{ transform: translateY(-160px); opacity: 1; }}
  }}

  .receipt-qr {{
    width: 95px;
    height: 95px;
    background: #000;
    margin: 10px auto;
    border: 3px solid #10B981;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.5);
  }}

  .feature-pill-strip {{
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 35px;
  }}
  .feature-pill {{
    background: rgba(16, 185, 129, 0.2);
    border: 1.5px solid #10B981;
    color: #34D399;
    padding: 10px 24px;
    border-radius: 999px;
    font-size: 22px;
    font-weight: 800;
  }}

  /* Scene 3: Us vs Them Comparison Matrix */
  .matrix-card {{
    background: rgba(15, 23, 42, 0.92);
    border: 2px solid rgba(255, 255, 255, 0.15);
    border-radius: 32px;
    padding: 36px;
    backdrop-filter: blur(30px);
    display: flex;
    flex-direction: column;
    gap: 24px;
  }}

  .matrix-item {{
    padding: 24px;
    border-radius: 22px;
  }}
  .matrix-them {{
    background: rgba(239, 68, 68, 0.12);
    border: 2px solid rgba(239, 68, 68, 0.35);
  }}
  .matrix-us {{
    background: rgba(16, 185, 129, 0.15);
    border: 2px solid #10B981;
  }}
  .matrix-header {{
    display: flex;
    justify-content: space-between;
    font-family: 'Outfit', sans-serif;
    font-size: 28px;
    font-weight: 900;
    margin-bottom: 10px;
  }}
  .matrix-sub {{
    font-size: 24px;
    color: #CBD5E1;
    line-height: 1.35;
  }}

  /* Scene 4: VIP Direct-Response Call to Action */
  .cta-hero {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: 40px;
  }}

  .cta-button {{
    background: #FF7A00;
    color: #0B0F19;
    font-family: 'Outfit', sans-serif;
    font-size: 44px;
    font-weight: 900;
    padding: 38px 60px;
    border-radius: 32px;
    text-transform: uppercase;
    box-shadow: 0 25px 60px rgba(255, 122, 0, 0.6);
    animation: cta-glow 2s infinite alternate;
    margin-bottom: 30px;
  }}

  @keyframes cta-glow {{
    0% {{ box-shadow: 0 20px 50px rgba(255, 122, 0, 0.4); }}
    100% {{ box-shadow: 0 35px 90px rgba(255, 122, 0, 0.85); }}
  }}

  .cta-subtext {{
    font-size: 32px;
    color: #CBD5E1;
    line-height: 1.4;
    max-width: 800px;
    margin-bottom: 40px;
  }}

  .trust-strip {{
    display: flex;
    gap: 20px;
  }}
  .trust-badge {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 12px 26px;
    border-radius: 999px;
    font-size: 20px;
    font-weight: 700;
    color: #94A3B8;
  }}

  /* Floating Subtitles Container (Above player controls safe zone) */
  .subtitle-container {{
    position: absolute;
    bottom: 110px;
    left: 60px;
    right: 60px;
    z-index: 20;
    height: 180px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 16px 20px;
    padding: 24px 36px;
    background: rgba(15, 23, 42, 0.88);
    border: 2px solid rgba(255, 122, 0, 0.45);
    border-radius: 28px;
    backdrop-filter: blur(30px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.8);
  }}

  .caption-word {{
    font-family: 'Outfit', sans-serif;
    font-size: 52px;
    font-weight: 900;
    color: #94A3B8;
    transition: all 0.12s ease-out;
    text-transform: uppercase;
  }}

  .caption-word.active {{
    color: #FFFFFF;
    background: #FF7A00;
    transform: scale(1.15);
    text-shadow: 0 0 30px rgba(255, 122, 0, 0.8), 0 0 10px #FFFFFF;
    padding: 4px 18px;
    border-radius: 14px;
  }}

  .caption-word.past {{ color: #F1F5F9; }}
</style>
</head>
<body>
  <!-- Fixed Top Header -->
  <div class="global-header">
    <div class="brand-pill">
      <img class="brand-logo-img" src="{logo_b64}" alt="Cafe QR" />
      <div class="brand-text">CAFE <span>QR 2.0</span></div>
    </div>
    <div class="top-badge">{badge}</div>
  </div>

  <!-- SCENE 1: The Hook (0.0s to {t1}s) -->
  <div class="scene active" id="scene_1" data-start="0.0" data-end="{t1}">
    <div class="bg-layer" style="background-image: url('{pos_counter_b64}'); filter: brightness(0.28) contrast(1.15);"></div>
    <div class="vignette"></div>
    <div style="position: relative; z-index: 2;">
      <div class="scene-hook-alert">🚨 COMMISSION ALERT</div>
      <h1 class="scene-title">{styled_head}</h1>
      <div class="breakdown-card">
        <div class="breakdown-row"><span>Customer Dine-in Bill</span><span>₹500.00</span></div>
        <div class="breakdown-row danger"><span>Aggregator Cut (28%)</span><span>-₹140.00 ❌</span></div>
        <div class="breakdown-row net"><span>Net Amount You Keep</span><span>₹360.00</span></div>
      </div>
    </div>
  </div>

  <!-- SCENE 2: Product In Action ({t1}s to {t2}s) -->
  <div class="scene" id="scene_2" data-start="{t1}" data-end="{t2}">
    <div class="bg-layer" style="background-image: url('{table_qr_b64}'); filter: brightness(0.25) contrast(1.15);"></div>
    <div class="vignette"></div>
    <div style="position: relative; z-index: 2;">
      <div class="scene-hook-alert" style="border-color: #10B981; color: #34D399; background: rgba(16, 185, 129, 0.2);">⚡ DIRECT TABLE ORDERING</div>
      <h1 class="scene-title">DINER SCANS. <span>0.8s THERMAL PRINT.</span></h1>
      <div class="hardware-center">
        <div class="printer-container">
          <img class="printer-img" src="{printer_b64}" alt="Thermal Printer" />
          <div class="animated-receipt">
            <div style="font-weight: bold; text-align: center;">CAFE QR 2.0</div>
            <div style="border-bottom: 1px dashed #666; margin: 4px 0;"></div>
            <div>TABLE #04 • 0.8s KOT</div>
            <div>TOTAL: ₹500.00</div>
            <div class="receipt-qr"></div>
            <div style="text-align: center; font-size: 11px; color: #10B981; font-weight: bold;">0% COMMISSION • 100% PROFIT</div>
          </div>
        </div>
      </div>
      <div class="feature-pill-strip">
        <div class="feature-pill">0% Commission</div>
        <div class="feature-pill">Direct UPI to Bank</div>
        <div class="feature-pill">0.8s KOT</div>
      </div>
    </div>
  </div>

  <!-- SCENE 3: Us vs Them Math ({t2}s to {t3}s) -->
  <div class="scene" id="scene_3" data-start="{t2}" data-end="{t3}">
    <div class="bg-layer" style="background-image: url('{bg_b64}'); filter: brightness(0.22) contrast(1.15);"></div>
    <div class="vignette"></div>
    <div style="position: relative; z-index: 2;">
      <div class="scene-hook-alert" style="border-color: #F59E0B; color: #FBBF24; background: rgba(245, 158, 11, 0.2);">💰 KEEP 100% OF YOUR REVENUE</div>
      <h1 class="scene-title">STOP PAYING <span>UPFRONT POS TRAPS</span></h1>
      <div class="matrix-card">
        <div class="matrix-item matrix-them">
          <div class="matrix-header" style="color: #F87171;"><span>TRADITIONAL POS & AGGREGATORS</span><span>❌</span></div>
          <div class="matrix-sub">₹15,000 Upfront + 28% Commission Cut on Every Bill + Forced Hardware Lock-in</div>
        </div>
        <div class="matrix-item matrix-us">
          <div class="matrix-header" style="color: #34D399;"><span>CAFE QR CORE BASE PLAN</span><span>✅</span></div>
          <div class="matrix-sub">Year 1: ₹2,498 (Setup Included) • Year 2+: Just ₹999/yr Forever • 0% Commission</div>
        </div>
      </div>
    </div>
  </div>

  <!-- SCENE 4: High Converting Call to Action ({t3}s to End) -->
  <div class="scene" id="scene_4" data-start="{t3}" data-end="999.0">
    <div class="bg-layer" style="background-image: url('{bg_b64}'); filter: brightness(0.18) contrast(1.2);"></div>
    <div class="vignette"></div>
    <div style="position: relative; z-index: 2;" class="cta-hero">
      <div class="scene-hook-alert" style="border-color: #FF7A00; color: #FFAA55; background: rgba(255, 122, 0, 0.25);">🚀 2-MINUTE AUDIT</div>
      <h1 class="scene-title" style="margin-bottom: 25px;">RECLAIM YOUR <span>PROFIT TODAY</span></h1>
      <div class="cta-button">{cta} 🚀</div>
      <p class="cta-subtext">Reply DEMO right now for a personalized 2-minute video audit of your restaurant's exact savings.</p>
      <div class="trust-strip">
        <div class="trust-badge">LLP Registered</div>
        <div class="trust-badge">0% Commission</div>
        <div class="trust-badge">Existing Hardware Compatible</div>
      </div>
    </div>
  </div>

  <!-- Whisper-Synced Kinetic Karaoke Captions (Rolling 4-Word Window) -->
  <div class="subtitle-container" id="subtitles"></div>

  <script>
    const words = {json.dumps(words_data)};
    const container = document.getElementById("subtitles");
    const scenes = document.querySelectorAll(".scene");

    let startTime = null;
    let lastChunkIdx = -1;

    function updateTimeline(timestamp) {{
      if (!startTime) startTime = timestamp;
      const elapsed = (timestamp - startTime) / 1000;

      // 1. Multi-Scene Switcher
      scenes.forEach(s => {{
        const start = parseFloat(s.getAttribute("data-start"));
        const end = parseFloat(s.getAttribute("data-end"));
        if (elapsed >= start && elapsed < end) {{
          if (!s.classList.contains("active")) s.classList.add("active");
        }} else {{
          if (s.classList.contains("active")) s.classList.remove("active");
        }}
      }});

      // 2. Whisper-Synced Rolling Karaoke Subtitles
      let activeIdx = words.findIndex(w => elapsed >= w.start && elapsed <= w.end);
      if (activeIdx === -1) {{
        for (let i = words.length - 1; i >= 0; i--) {{
          if (elapsed > words[i].end) {{
            activeIdx = i;
            break;
          }}
        }}
      }}
      if (activeIdx === -1) activeIdx = 0;

      const chunkSize = 4;
      const chunkIdx = Math.floor(activeIdx / chunkSize);

      if (chunkIdx !== lastChunkIdx) {{
        lastChunkIdx = chunkIdx;
        container.innerHTML = "";
        const start = chunkIdx * chunkSize;
        const end = Math.min(start + chunkSize, words.length);
        for (let i = start; i < end; i++) {{
          const span = document.createElement("span");
          span.id = "w_" + i;
          span.className = "caption-word";
          span.innerText = words[i].word;
          container.appendChild(span);
        }}
      }}

      const start = chunkIdx * chunkSize;
      const end = Math.min(start + chunkSize, words.length);
      for (let i = start; i < end; i++) {{
        const el = document.getElementById("w_" + i);
        if (!el) continue;
        const item = words[i];
        if (elapsed >= item.start && elapsed <= item.end) {{
          el.className = "caption-word active";
        }} else if (elapsed > item.end) {{
          el.className = "caption-word past";
        }} else {{
          el.className = "caption-word";
        }}
      }}

      requestAnimationFrame(updateTimeline);
    }}

    window.startReel = function() {{
      startTime = performance.now();
      requestAnimationFrame(updateTimeline);
    }};
  </script>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Step 5: Record Multi-Scene Kinetic Video via Playwright Chromium
    print(f"🎬 [ReelEngine] Recording {total_duration:.1f}s multi-scene kinetic video via Playwright...")
    video_raw_dir = temp_dir / "raw_video"
    video_raw_dir.mkdir(parents=True, exist_ok=True)
    raw_video_file = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1,
            record_video_dir=str(video_raw_dir),
            record_video_size={"width": 1080, "height": 1920}
        )
        t_page_open = time.time()
        page = context.new_page()
        page.set_viewport_size({"width": 1080, "height": 1920})
        page.goto(f"file:///{html_path}", wait_until="load")
        page.wait_for_timeout(150)  # Wait for dark frame 0 to paint firmly

        # Exact lead-in delay from recorder start to animation start
        lead_in_delay = time.time() - t_page_open
        print(f"⏱️ [ReelEngine] Calculated lead-in delay: {lead_in_delay:.3f}s (Trimming in FFmpeg for zero white screen & perfect sync)")

        # Trigger animation clock
        page.evaluate("window.startReel()")

        page.wait_for_timeout(int(total_duration * 1000) + 400)
        context.close()
        raw_video_file = page.video.path()
        browser.close()

    # Step 6: Mux Video with Multi-Track Audio (Voice + Ducked BGM) via FFmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    audio_profile = creative_data.get("audio_profile", {})
    situation = audio_profile.get("situation", "BREAKING_TENSION")
    search_query = audio_profile.get("search_query") or "price disruption beat"
    bgm_path = music_fetcher.fetch_or_search_music(search_query=search_query, situation_key=situation)

    # Fallback to verified instrumental studio track if fetched file doesn't exist
    if not bgm_path or not os.path.exists(bgm_path):
        fallback_bgm = ASSETS_DIR / "audio" / "bgm_tension_beat.mp3"
        if fallback_bgm.exists():
            bgm_path = str(fallback_bgm)

    if bgm_path and os.path.exists(bgm_path):
        print(f"🎵 [ReelEngine] Muxing multi-track audio with sidechain dynamic ducking ({os.path.basename(bgm_path)})...")
        cmd = [
            ffmpeg_exe, "-y",
            "-ss", f"{lead_in_delay:.3f}",
            "-i", str(raw_video_file),
            "-i", str(mp3_path),
            "-stream_loop", "-1",
            "-i", str(bgm_path),
            "-filter_complex", (
                f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.0,asplit=2[v_main][v_sc];"
                f"[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=0.22[bgm_base];"
                f"[bgm_base][v_sc]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=300[bgm_ducked];"
                f"[v_main][bgm_ducked]amix=inputs=2:duration=first:weights=1.0 1.0:normalize=0[a]"
            ),
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_mp4)
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y",
            "-ss", f"{lead_in_delay:.3f}",
            "-i", str(raw_video_file),
            "-i", str(mp3_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_mp4)
        ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Clean up temp directory
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    print(f"✅ Multi-Scene Kinetic Reel MP4 generated: {output_mp4.name} (1080x1920)")
    return str(output_mp4)

if __name__ == "__main__":
    test_creative = {
        "headline": "STOP PAYING ₹15,000 UPFRONT FOR POS",
        "subtext": "Petpooja charges ₹15,000 upfront + ₹3,000 yearly renewals. Switch to Cafe QR ₹99/mo.",
        "badge": "⚡ HARDWARE & SPEED FLEX",
        "script": "Are you really still paying 15,000 rupees upfront for POS software? And another 3,000 rupees every year just to keep it running? Switch to Cafe QR today for just 99 rupees a month."
    }
    video = render_reel_video(test_creative, filename="human_proof_reel_test.mp4")
    print(f"Video file ready: {video}")
