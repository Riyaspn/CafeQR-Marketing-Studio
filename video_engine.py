import os
import uuid
import asyncio
import subprocess
import base64
from pathlib import Path
import imageio_ffmpeg
import edge_tts
from playwright.sync_api import sync_playwright
from config import BASE_DIR, DRAFTS_DIR, ASSETS_DIR

def _get_b64_asset(filename, mime="image/png"):
    p = ASSETS_DIR / filename
    if p.exists():
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

def render_reel_frame(headline, subtext, badge_text, step_text, output_png_path, style="human_ugc"):
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
  <div class="center-content">
    <div class="eyebrow">⚡ STOP GIVING 28% TO MONOPOLIES</div>
    <h1 class="headline">{headline}</h1>
    <p class="subtext">{subtext}</p>
    
    <!-- Real Hardware Proof Card -->
    <div class="proof-card">
      <img class="printer-thumb" src="{printer_b64}" alt="Cafe QR Thermal Printer" />
      <div class="proof-details">
        <div class="proof-title">0.8-SEC SUB-SECOND KOT</div>
        <div class="proof-sub">Diner scans Table QR &rarr; Instant thermal print &rarr; 0% Commission</div>
      </div>
    </div>
  </div>

  <!-- Bottom CTA -->
  <div class="bottom-cta">
    COMMENT 'DEMO' FOR FREE 7-DAY TRIAL 🚀
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
    Renders a complete 9:16 vertical MP4 video Reel:
    1. Generates neural voiceover (edge-tts)
    2. Measures audio duration
    3. Renders high-impact 1080x1920 visuals with real logo & hardware
    4. Muxes with FFmpeg into high-quality H.264 MP4
    """
    uid = uuid.uuid4().hex[:8]
    if not filename:
        filename = f"reel_{uid}.mp4"

    mp3_path = DRAFTS_DIR / f"voice_{uid}.mp3"
    frame_path = DRAFTS_DIR / f"frame_{uid}.png"
    output_mp4 = DRAFTS_DIR / filename

    script_text = creative_data.get("script", "Stop giving 28% to aggregators. Switch to Cafe QR today.")
    headline = creative_data.get("headline", "RESTAURANT PROFIT ALERT")
    subtext = creative_data.get("subtext", "Stop losing 28% per order.")
    badge = creative_data.get("badge", "🚨 F&B PROFIT ALERT")
    step = "0% Commission Direct Ordering • 0.8s Thermal KOT"

    # Step 1: Synthesize Audio
    asyncio.run(synthesize_voiceover(script_text, mp3_path, voice_key))

    # Step 2: Render Visual Frame with Real Logo
    words = headline.split()
    if len(words) > 2:
        styled_head = " ".join(words[:-2]) + f" <span>{' '.join(words[-2:])}</span>"
    else:
        styled_head = f"<span>{headline}</span>"

    render_reel_frame(styled_head, subtext, badge, step, frame_path)

    # Step 3: FFmpeg Video Encoding with pan-zoom kinetic motion
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-loop", "1",
        "-i", str(frame_path),
        "-i", str(mp3_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_mp4)
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Clean up intermediate frame and voice file
    if frame_path.exists():
        frame_path.unlink()
    if mp3_path.exists():
        mp3_path.unlink()

    print(f"🎬 Reel MP4 generated: {output_mp4.name} (1080x1920)")
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
