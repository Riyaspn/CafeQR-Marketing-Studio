# 🚀 Cafe QR 2.0 — Viral Marketing & Content Studio
### *100% Free, Zero-Subscription Automated Content Factory for Instagram & Facebook*

A completely standalone, zero-cost marketing automation engine designed specifically for **Cafe QR 2.0**. It turns real-time Indian F&B news and controversies into viral graphic posters, 9:16 short-form video Reels with neural voiceovers, and publishes them directly to Facebook & Instagram via the Meta Graph API.

---

## ⚡ Key Capabilities & Free Technology Stack

| Capability | Free Industry Standard Tech | Zero-Cost Benefit |
| :--- | :--- | :--- |
| **Live Trend Radar** | Google News RSS & Reddit APIs | Real-time Swiggy/Zomato fee hikes & GST controversies without paid news APIs |
| **Creative Brain & Copy** | Hormozi F&B Formulas + Gemini AI | Generates viral hooks, comparison angles, captions, and hashtags automatically |
| **High-Res Graphic Posters** | Playwright Headless Chromium | Renders pixel-perfect 1080x1350 (IG 4:5 Portrait) & 1080x1080 graphic cards |
| **9:16 Video Reels** | `edge-tts` (Microsoft Neural Engine) | Authentic Indian English neural voices (`en-IN-PrabhatNeural`, `en-IN-NeerjaNeural`) with zero cost & zero API keys |
| **Video Compositing** | `imageio-ffmpeg` (Bundled FFmpeg 7.1) | Renders 1080x1920 MP4 Reels with kinetic animated captions and audio muxing |
| **Meta Graph API** | Meta Graph API v22.0 | Direct multipart publishing to Facebook Pages & Instagram Business accounts |
| **Interactive Studio UI** | Python HTTP + Modern Vanilla JS | Side-by-side visual preview, editable copy, and 1-click "Approve & Publish" |

---

## 📂 Folder Structure

```
c:\RIYAS\Sharp INtell\CafeQR-Marketing-Studio\
├── run_studio.bat             # 1-Click launcher for Windows
├── studio_server.py           # Local Web Server on port 8899
├── trend_radar.py             # Free Google News RSS & Reddit controversy scraper
├── creative_brain.py          # AI Hook & Viral Script Generator (Gemini + Hormozi rules)
├── poster_engine.py           # Playwright 1080x1350 HTML/CSS graphic renderer
├── video_engine.py            # edge-tts + FFmpeg 9:16 vertical Reel synthesizer
├── meta_publisher.py          # Meta Graph API publisher for Facebook & Instagram
├── config.py                  # Core path and environment configuration
├── .env                       # Meta access tokens, Page ID, Gemini keys
├── setup_assets.py            # Asset loader
├── templates/                 # High-impact HTML5/CSS3 templates for posters
│   ├── news_alert.html        # Breaking F&B alert card
│   ├── us_vs_them.html        # Legacy POS vs Cafe QR comparison matrix
│   └── feature_spotlight.html # 0.8s Thermal KOT & Speed Flex
├── assets/                    # Cafe QR brand logos, printer mockups, sample visuals
├── drafts/                    # Staged high-res PNG posters and MP4 reels
└── web/                       # Modern Glassmorphic Studio Dashboard UI
    ├── index.html
    ├── style.css
    └── app.js
```

---

## 🎯 How to Launch & Use the Marketing Studio

### Step 1: Launch the Studio
Double-click `run_studio.bat` or run in terminal:
```powershell
cd "c:\RIYAS\Sharp INtell\CafeQR-Marketing-Studio"
python studio_server.py
```
The browser will automatically open: **`http://localhost:8899`**

### Step 2: Pick a Live Trend or Custom Topic
- The left sidebar displays live headlines (e.g. *"Ordering food online gets costlier as Swiggy raises platform fee"*).
- Click any headline, or type a custom topic in the input box.
- The system automatically analyzes the controversy and generates:
  1. A **1080x1350 high-impact graphic poster**.
  2. A **9:16 vertical MP4 video Reel** with natural Indian English neural voiceover.
  3. A compelling **caption with hashtags and WhatsApp demo link**.

### Step 3: Review & Edit in the Workbench
- Toggle between `🖼️ High-Res Poster` and `🎬 9:16 Video Reel` to preview your creatives.
- Tweak the headline, subtext, script, voiceover artist, or caption.
- Click **"🔄 Re-render Visual"** or **"🎬 Re-render Video"** to update in seconds.

### Step 4: 1-Click Publish to Meta
- Select **Facebook Page** and/or **Instagram**.
- Click **"🚀 APPROVE & PUBLISH TO SOCIAL MEDIA"**.
- The post is published directly to your accounts with live confirmation!

---

## 🔑 Meta Access Token Refresh Guide

When your Meta Access Token expires:
1. Open the **Meta Graph API Explorer**: [developers.facebook.com/tools/explorer/](https://developers.facebook.com/tools/explorer/)
2. Select your Cafe QR App and Facebook Page.
3. Grant permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
4. Click **Generate Access Token**.
5. In the Marketing Studio UI, click **"⚙️ API Settings"**, paste the new token, and click **Save & Verify Connection**.
