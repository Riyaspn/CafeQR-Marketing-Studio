import os
import json
import re
import requests
from config import (
    BRAND_NAME, BRAND_URL, WHATSAPP_DEMO_LINK,
    NVIDIA_API_KEY, NVIDIA_BASE_URL, MODEL_PRIMARY, MODEL_FALLBACK,
    GEMINI_API_KEY
)
from knowledge_vault.evaluator import score_creative

def call_nvidia_nim(messages, model=None, temperature=0.3, max_tokens=1000, timeout=30):
    """
    High-resilience client for NVIDIA NIM API with automated fallback.
    Tries MODEL_PRIMARY first, then falls back to MODEL_FALLBACK.
    """
    api_key = NVIDIA_API_KEY
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not configured in .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = f"{NVIDIA_BASE_URL.rstrip('/')}/chat/completions"

    models_to_try = [model or MODEL_PRIMARY]
    if MODEL_FALLBACK not in models_to_try:
        models_to_try.append(MODEL_FALLBACK)

    last_error = None
    for m in models_to_try:
        payload = {
            "model": m,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 200:
                raw_text = r.json()["choices"][0]["message"]["content"]
                return raw_text
            else:
                last_error = f"Model {m} returned status {r.status_code}: {r.text[:120]}"
        except Exception as e:
            last_error = f"Model {m} exception: {str(e)[:120]}"

    raise RuntimeError(f"All NVIDIA NIM models failed. Last error: {last_error}")

def clean_json_response(raw_text):
    """
    Strips markdown code blocks and whitespace to cleanly parse JSON from LLM output.
    """
    text = raw_text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    return json.loads(text.strip())

def analyze_audio_situation(category, headline="", script=""):
    """
    Dynamic AI Sound Director: Uses NVIDIA NIM LLM to analyze the emotional
    and acoustic situation of each campaign, generating tailored Pixabay search
    queries, BPM targets, and timed foley sound cues. Zero hardcoded if/else branches.
    """
    prompt = f"""
Analyze the marketing reel script and headline below. Act as an award-winning Sound Director for social media video ads:
Headline: "{headline}"
Reel Script: "{script}"
Category: "{category}"

Determine the optimal acoustic profile, background music genre, and foley sound effect cue points.
Return ONLY valid JSON matching this schema:
{{
  "situation": "PRICE_DISRUPTION | TECH_SPEED_FLEX | BREAKING_TENSION | CAFE_AMBIANCE | PEAK_RUSH_FIGHT",
  "situation_label": "Short bold label with emoji (e.g. ⚡ Kinetic Hardware Pulse)",
  "search_query": "3-4 concise keywords for Pixabay music search (e.g. 'electronic bass beat', 'ambient dramatic synth', 'chill acoustic guitar')",
  "title": "Descriptive title for track mood",
  "genre": "Genre description",
  "trending_ig_tip": "Recommended trending Instagram audio style or commercial song recommendation",
  "bgm_volume": 0.18,
  "foley_cues": [
    {{"time_sec": 4.5, "sound": "printer_cut", "description": "Rapid thermal printer receipt ejection chhhk"}},
    {{"time_sec": 12.0, "sound": "upi_chime", "description": "Google Pay instant payment received chime"}}
  ]
}}
"""
    try:
        messages = [
            {"role": "system", "content": "You are a professional film and commercial ad Sound Director. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ]
        raw = call_nvidia_nim(messages, temperature=0.2, max_tokens=400, timeout=20)
        profile = clean_json_response(raw)
        return profile
    except Exception as e:
        # Dynamic fallback if API connection flickers
        clean_words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', f"{headline} {script}".lower()) if w not in ["with", "from", "that", "this", "have", "your"]]
        kw = " ".join(clean_words[:3]) if clean_words else "ambient electronic synth"
        return {
            "situation": "DYNAMIC_MATCH",
            "situation_label": "🎵 Dynamic Acoustic Match",
            "search_query": f"{kw} electronic beat",
            "title": "Tailored Kinetic Beat",
            "genre": "Dynamic Electronic / Modern",
            "trending_ig_tip": "Trending Commercial Reel Audio (Fast Paced)",
            "bgm_volume": 0.18,
            "foley_cues": [
                {"time_sec": 4.0, "sound": "printer_cut", "description": "Thermal printer receipt cut"},
                {"time_sec": 14.0, "sound": "upi_chime", "description": "UPI payment chime"}
            ]
        }

def generate_creative_campaign(topic_item):
    """
    Autonomous Multi-Stage Agentic Creative Brain:
    1. Strategic Synthesis & Awareness Stage Assignment (Eugene Schwartz).
    2. Creative Drafting adhering to the 4 Legendary Ad Masters (Hormozi, Ogilvy, Schwartz, Williams).
    3. Autonomous Reflection & Self-Critique Loop (Auditing with score_creative and self-correcting up to 3 passes).
    4. Dynamic AI Sound Direction.
    """
    title = topic_item.get("title", "Indian Business Billing & Margin Squeeze")
    source = topic_item.get("source", "Industry Intel")
    category = topic_item.get("category", "BUSINESS_OPERATIONS")
    vertical_hint = topic_item.get("vertical", "Multi-Vertical Retail & Cafes")

    system_persona = f"""You are the Chief Direct-Response Marketing Director for Cafe QR (LLP registered Indian business tech platform, https://cafeqr.in).
Cafe QR is the modern, affordable billing, QR and operations software used across India by:
- Restaurants, Cafes & Cloud Kitchens (Table QR ordering, 0.8s thermal KOT, 0% commission direct delivery)
- Bakeries & Confectioneries (Batch expiry management, barcode scanning, fast checkout)
- Car Washes & Auto Detailing (Digital job card tokens, WhatsApp vehicle status alerts, dynamic UPI)
- Boutiques & Retail Stores (Barcode inventory tags, instant billing, customer Udhaar khata tabs)
- Salons, Spas & QSRs (Appointment billing, stylist commissions, customer CRM)

CAFE QR AUTHENTIC SPECS & PRICING:
- Official App Name: strictly "Cafe QR" (never "Cafe QR POS" or "Cafe QR 2.0").
- Core Base Plan: Year 1 is ₹2,498 (₹999 Annual Subscription + ₹1,499 One-Time Setup & Onboarding).
- Year 2 & Beyond Renewal: Just ₹999/year! (Renewal under ₹1,000/year forever; setup fee is never paid again).
- Base Plan includes: Advanced Billing, Table QR Ordering, Digital Menus, & Quick-Commerce Delivery Integration!
- Modular bolt-on add-ons: KOT Kitchen Order Tickets (₹499/yr), Credit Ledger Udhaar Tabs (₹499/yr), Customer CRM & Loyalty (₹999/yr), Inventory ERP (₹1,999/yr), Barcode Scanning (₹999/yr), HR & Staff Payroll (₹1,999/yr).
- Direct delivery: 0% Commission direct table ordering (Swiggy/Zomato charge 25% to 30%).
- Hardware speed: 0.8s ESC/POS thermal printing with dynamic UPI QR on receipts.
- Competitor contrast: Petpooja and legacy retail ERPs trap merchants with ₹15,000 to ₹30,000 upfront charges + forced yearly renewals that never go down.
- Official links: Play Store: https://play.google.com/store/apps/details?id=com.cafeqr.app&hl=en_IN | Web: https://cafeqr.in | Instagram: https://www.instagram.com/cafe_qr_

THE 4 LEGENDARY AD MASTERS & ANTI-AI CONSTITUTION:
1. Alex Hormozi ($100M Leads): Hook-Retain-Reward pacing. End with frictionless Grand Slam lead magnet (e.g. Reply DEMO for 2-minute unedited video audit).
2. David Ogilvy (Ogilvy on Advertising): Headlines must carry news or specific numbers (max 7 words, ALL CAPS, no cute puns). Caption must be informative and fact-dense. Respect the merchant; no hollow superlatives.
3. Eugene Schwartz (Breakthrough Advertising): Channel existing business margin desire into Cafe QR's Unique Mechanism (0.8s direct thermal print, dynamic UPI QR on bill, ₹999/yr renewal, barcode billing). Target the prospect's awareness stage.
4. Roy H. Williams (Wizard of Ads): Appeal to the 3 Banks of the Mind using sensory details (sight: glowing neon UPI QR, barcode scan line; sound: zipp-zipp thermal printer, GPay chime; feeling: rush relief). Speak in rhythmic, authentic counter-floor cadence.
5. Zero em dashes (never use '—'; use plain commas, colons, or periods).
6. Zero banned AI words (never use revolutionize, elevate, robust, seamless, cutting-edge, game-changer, innovate, empower, foster, delve, pivotal, crucial, vital, tapestry).
7. Zero contrast framing (never use 'It is not X, it is Y' or 'Not only X, but also Y'). State positive factual claims directly.
8. One Action Rule: Single clear CTA telling the merchant what they get.
"""

    draft_prompt = f"""
NEWS TOPIC TO TREND-JACK:
"{title}"
Source: {source}
Category: {category}
Target Domain/Vertical: {vertical_hint}

Craft a complete viral direct-response campaign in strict JSON format:
{{
  "target_vertical": "{vertical_hint}",
  "headline": "Bold punchy headline in ALL CAPS, max 7 words with news or specific rupee figures (Ogilvy 80/20 rule)",
  "subtext": "Sharp 1-line sub-hook highlighting the merchant pain point with exact numbers",
  "badge": "Short badge tag (e.g. 🚨 F&B PROFIT ALERT, 🥐 BAKERY RUSH ALERT, 🚗 CAR WASH DETECTIVE, or ⚡ HARDWARE FLEX)",
  "script": "A 15-20 second conversational voiceover script for Instagram Reels with Williams sensory cues. Ends with 'Reply DEMO for 2-minute unedited video audit'.",
  "caption": "Full Instagram/Facebook caption following Ogilvy's Informative Caption Law with hook, bullet points, transparent pricing (Year 1 ₹2,498 / Year 2+ ₹999/yr), and hashtags",
  "comparison": {{
    "title": "Specific comparison title tailored to the news",
    "them_label": "The specific competitor or legacy manual way",
    "them_points": [
      "Point 1 with exact rupee loss or flaw",
      "Point 2 with operational bottleneck or lock-in",
      "Point 3 with customer data loss or fee trap"
    ],
    "us_label": "Cafe QR Direct Solution",
    "us_points": [
      "Point 1 with 0% commission or Year 1 ₹2,498 / Year 2+ ₹999/yr renewal",
      "Point 2 with sub-second thermal print or barcode speed",
      "Point 3 with 100% customer CRM & UPI settlement"
    ]
  }},
  "cta": "Reply DEMO for 2-Minute Video Audit"
}}
Return ONLY valid JSON.
"""

    messages = [
        {"role": "system", "content": system_persona},
        {"role": "user", "content": draft_prompt}
    ]

    # --- Autonomous Reflection & Self-Critique Loop ---
    max_reflection_turns = 3
    final_campaign = None

    for iteration in range(1, max_reflection_turns + 1):
        raw_output = call_nvidia_nim(messages, temperature=0.25, max_tokens=1100, timeout=35)
        campaign_data = clean_json_response(raw_output)

        # Audit against 10-Point Viral Rubric and 4 Legendary Masters
        audit = score_creative(campaign_data)
        campaign_data["evaluation"] = audit
        campaign_data["source_tag"] = source
        campaign_data["news_title"] = title

        score = audit.get("score", 0.0)
        recs = audit.get("recommendations", [])
        masters = audit.get("legendary_masters_audit", {})
        all_passed = all(status == "PASS" for status in masters.values())

        if score >= 9.5 and all_passed:
            campaign_data["reflection_passes"] = iteration
            final_campaign = campaign_data
            break

        # If defects found, feed critique back to LLM for surgical correction
        critique_msg = f"""
CRITIQUE OF YOUR DRAFT (Score: {score}/10):
The draft has the following issues that must be corrected immediately:
{json.dumps(recs, indent=2)}
Legendary Masters Status:
{json.dumps(masters, indent=2)}

Please revise the entire JSON to address every single recommendation.
Ensure:
- Zero em dashes (—).
- Zero banned AI words.
- Ogilvy headline has hard numbers or news and is 7 words or fewer.
- Williams sensory cues (thermal printer sound, glowing UPI QR, GPay chime) are clearly audible in the script.
- Hormozi CTA offers an unedited 2-minute video audit or trial.
- Comparison points are detailed and tailored to this specific topic.

Return ONLY the corrected valid JSON.
"""
        messages.append({"role": "assistant", "content": raw_output})
        messages.append({"role": "user", "content": critique_msg})
        final_campaign = campaign_data

    # Finalize with Freeform Generative Poster HTML & Dynamic Audio Profile
    print("🎨 [CreativeBrain] Invoking AI Art Director for bespoke Freeform HTML/CSS poster...")
    final_campaign["poster_html"] = generate_poster_html(final_campaign, topic_item)
    final_campaign["audio_profile"] = analyze_audio_situation(
        category,
        final_campaign.get("headline", ""),
        final_campaign.get("script", "")
    )

    return final_campaign

def generate_poster_html(campaign_data, topic_item=None):
    """
    Autonomous AI Art Director:
    Synthesizes a production-grade 1080x1350 HTML+CSS poster for Cafe QR.
    Combines an ultra-premium luxury dark design shell with an AI-generated bespoke visual centerpiece card
    tailored to the business vertical (Restaurant, Bakery, Car Wash, Boutique, Salon).
    """
    topic_item = topic_item or {}
    headline = campaign_data.get("headline", "STOP PAYING ₹15,000 UPFRONT FOR BILLING")
    subtext = campaign_data.get("subtext", "Switch to Cafe QR Year 1 ₹2,498 and ₹999/year renewal forever.")
    badge = campaign_data.get("badge", "⚡ BILLING DISRUPTION")
    vertical = campaign_data.get("target_vertical", topic_item.get("vertical", "Multi-Vertical Retail & Services"))
    cta = campaign_data.get("cta", "Reply DEMO for 2-Minute Audit")
    comparison = campaign_data.get("comparison", {})
    them_label = comparison.get("them_label", "Legacy Systems & Aggregators")
    them_points = comparison.get("them_points", ["High upfront costs", "Forced yearly lock-in", "Hidden fee traps"])
    us_label = comparison.get("us_label", "Cafe QR Direct Solution")
    us_points = comparison.get("us_points", ["Year 1 ₹2,498 (Setup Included)", "Year 2+ ₹999/yr renewal forever", "100% data ownership"])

    # Format Headline with vibrant orange highlight span on the last 2-3 words/numbers
    words = headline.split()
    if len(words) > 2:
        split_idx = max(len(words) - 3, 2)
        head_first = " ".join(words[:split_idx])
        head_last = " ".join(words[split_idx:])
        styled_headline = f"{head_first} <span>{head_last}</span>"
    else:
        styled_headline = f"<span>{headline}</span>"

    centerpiece_html = None
    art_prompt = f"""
Act as an award-winning Senior Art Director for Cafe QR (Official Site: www.cafeqr.in).
Generate a custom visual evidence card in pure clean HTML for this direct-response Instagram poster (1080x1350).

VERTICAL: {vertical}
TOPIC: {topic_item.get('title', headline)}
THEIR FLAWS ({them_label}): {json.dumps(them_points)}
CAFE QR ADVANTAGE ({us_label}): {json.dumps(us_points)}

Generate ONLY the central evidence card HTML. Choose the most compelling visual for this topic and vertical:
Option A: A 2-column head-to-head comparison grid with red ✕ icons (.card-them) and emerald green ✓ icons (.card-us).
Option B: A realistic CSS thermal receipt calculation card (.receipt-card) showing exact rupee numbers (e.g. commission fee deduction vs keeping 100% with Cafe QR).
Option C: A digital service token / WhatsApp job card mockup (.token-card) for car washes or service appointments.
Option D: A fresh batch expiry or barcode scanner inventory tag card (.barcode-card) for bakeries or boutiques.

Use class names: .comparison-grid, .card-them, .card-us, .card-title, .them-title, .us-title, .point-item, .icon-cross, .icon-check, .receipt-card, .receipt-line.
Return ONLY the HTML for the card (e.g. <div class="comparison-grid">...</div>).
Do NOT include markdown fences, DO NOT include <html> or <body> tags.
"""
    messages = [
        {"role": "system", "content": "You are a master UI/UX visual designer. Output strictly HTML for the centerpiece element."},
        {"role": "user", "content": art_prompt}
    ]

    try:
        raw_centerpiece = call_nvidia_nim(messages, temperature=0.2, max_tokens=1100, timeout=30)
        cleaned_centerpiece = raw_centerpiece.replace("```html", "").replace("```", "").strip()
        if "<div" in cleaned_centerpiece and "</div>" in cleaned_centerpiece:
            centerpiece_html = cleaned_centerpiece
            print("🎨 [CreativeBrain] Bespoke centerpiece card successfully generated by AI Art Director.")
    except Exception as e:
        print(f"[CreativeBrain] AI Centerpiece generation warning: {e}. Using structured fallback.")

    # Resilient fallback if LLM times out or card is empty
    if not centerpiece_html:
        them_pts_html = "".join([f'<div class="point-item"><span class="icon-cross">✕</span><span>{pt}</span></div>' for pt in them_points])
        us_pts_html = "".join([f'<div class="point-item"><span class="icon-check">✓</span><span>{pt}</span></div>' for pt in us_points])
        centerpiece_html = f"""
    <div class="comparison-grid">
      <div class="card-them">
        <div class="card-title them-title">
          <span>{them_label}</span>
          <span style="font-size: 15px; background: rgba(239,68,68,0.2); padding: 4px 10px; border-radius: 8px;">TRAP</span>
        </div>
        {them_pts_html}
      </div>
      <div class="card-us">
        <div class="card-title us-title">
          <span>{us_label}</span>
          <span style="font-size: 15px; background: rgba(16,185,129,0.2); padding: 4px 10px; border-radius: 8px;">PROFIT</span>
        </div>
        {us_pts_html}
      </div>
    </div>
"""

    full_poster_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1350px;
    background: #080C14;
    color: #F8FAFC;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    overflow: hidden;
    padding: 64px 60px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .ambient-glow {{
    position: absolute;
    width: 750px;
    height: 750px;
    top: 15%;
    right: -150px;
    background: radial-gradient(circle, rgba(255, 122, 0, 0.20) 0%, transparent 70%);
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
  }}
  .ambient-glow-2 {{
    position: absolute;
    width: 600px;
    height: 600px;
    bottom: 10%;
    left: -120px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%);
    filter: blur(90px);
    pointer-events: none;
    z-index: 0;
  }}
  .grid-bg {{
    position: absolute;
    inset: 0;
    background-image: linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }}
  .z2 {{ position: relative; z-index: 2; }}

  /* Header */
  .header-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .brand-group {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}
  .brand-logo {{
    height: 64px;
    width: auto;
    border-radius: 14px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  }}
  .brand-text {{
    display: flex;
    flex-direction: column;
  }}
  .brand-name {{
    font-family: 'Outfit', sans-serif;
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 0.5px;
    color: #FFFFFF;
  }}
  .brand-sub {{
    font-size: 13px;
    color: #94A3B8;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}
  .badge-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 122, 0, 0.15);
    border: 1.5px solid rgba(255, 122, 0, 0.45);
    color: #FF7A00;
    font-size: 15px;
    font-weight: 800;
    padding: 8px 22px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}

  /* Hero Section */
  .hero-section {{
    margin: 20px 0 10px 0;
  }}
  .headline-main {{
    font-family: 'Outfit', sans-serif;
    font-size: 58px;
    font-weight: 900;
    line-height: 1.1;
    text-transform: uppercase;
    letter-spacing: -1px;
    margin-bottom: 12px;
  }}
  .headline-main span {{
    color: #FF7A00;
  }}
  .subtext-main {{
    font-size: 23px;
    color: #94A3B8;
    line-height: 1.4;
  }}

  /* Centerpiece Card Container */
  .centerpiece-box {{
    margin: 16px 0;
  }}
  .comparison-grid, .grid-container {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }}
  .card-them, .them-card {{
    background: rgba(239, 68, 68, 0.05);
    border: 1.5px solid rgba(239, 68, 68, 0.35);
    border-radius: 24px;
    padding: 28px;
  }}
  .card-us, .us-card {{
    background: linear-gradient(180deg, rgba(255, 122, 0, 0.12) 0%, rgba(16, 185, 129, 0.08) 100%);
    border: 2px solid #FF7A00;
    border-radius: 24px;
    padding: 28px;
    box-shadow: 0 10px 30px rgba(255, 122, 0, 0.15);
  }}
  .card-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .them-title {{ color: #F87171; }}
  .us-title {{ color: #34D399; }}
  .point-item {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    font-size: 17px;
    line-height: 1.4;
    margin-bottom: 14px;
    color: #E2E8F0;
  }}
  .icon-cross {{ color: #EF4444; font-weight: bold; font-size: 18px; min-width: 20px; }}
  .icon-check {{ color: #10B981; font-weight: bold; font-size: 18px; min-width: 20px; }}

  /* Receipt and Card Styles */
  .receipt-card {{
    background: #FFFFFF;
    color: #0F172A;
    border-radius: 20px;
    padding: 32px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    max-width: 700px;
    margin: 0 auto;
  }}
  .receipt-line {{
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px dashed #CBD5E1;
    font-size: 18px;
  }}

  /* Pricing Pill Bar */
  .pricing-bar {{
    background: rgba(255, 255, 255, 0.04);
    border: 1.5px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
  }}
  .pricing-item {{
    display: flex;
    flex-direction: column;
  }}
  .pricing-label {{
    font-size: 12px;
    color: #94A3B8;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
  }}
  .pricing-val {{
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 900;
    color: #FFFFFF;
  }}
  .pricing-val.highlight {{
    color: #FF7A00;
  }}

  /* CTA Button */
  .btn-cta {{
    display: block;
    width: 100%;
    background: linear-gradient(135deg, #FF7A00 0%, #FF5500 100%);
    color: #FFFFFF;
    font-family: 'Outfit', sans-serif;
    font-size: 26px;
    font-weight: 900;
    text-align: center;
    padding: 22px 30px;
    border-radius: 18px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 12px 36px rgba(255, 122, 0, 0.38);
    text-decoration: none;
  }}
  .trust-strip {{
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-top: 14px;
    font-size: 14px;
    color: #94A3B8;
    font-weight: 600;
  }}
</style>
</head>
<body>
  <div class="ambient-glow"></div>
  <div class="ambient-glow-2"></div>
  <div class="grid-bg"></div>

  <div class="z2 header-row">
    <div class="brand-group">
      <img src="{{{{logo_img}}}}" alt="Cafe QR" class="brand-logo" />
      <div class="brand-text">
        <span class="brand-name">CAFE QR</span>
        <span class="brand-sub">www.cafeqr.in • LLP Registered</span>
      </div>
    </div>
    <div class="badge-pill">{badge}</div>
  </div>

  <div class="z2 hero-section">
    <h1 class="headline-main">{styled_headline}</h1>
    <p class="subtext-main">{subtext}</p>
  </div>

  <div class="z2 centerpiece-box">
    {centerpiece_html}
  </div>

  <div class="z2">
    <div class="pricing-bar">
      <div class="pricing-item">
        <span class="pricing-label">Year 1 Base Plan</span>
        <span class="pricing-val highlight">₹2,498 <span style="font-size: 13px; font-weight: normal; color: #94A3B8;">(Setup Included)</span></span>
      </div>
      <div style="height: 30px; width: 1px; background: rgba(255,255,255,0.1);"></div>
      <div class="pricing-item">
        <span class="pricing-label">Year 2+ Renewal</span>
        <span class="pricing-val" style="color: #10B981;">₹999/Year <span style="font-size: 13px; font-weight: normal; color: #94A3B8;">Forever</span></span>
      </div>
      <div style="height: 30px; width: 1px; background: rgba(255,255,255,0.1);"></div>
      <div class="pricing-item">
        <span class="pricing-label">Commission Fee</span>
        <span class="pricing-val" style="color: #38BDF8;">0% <span style="font-size: 13px; font-weight: normal; color: #94A3B8;">Direct UPI</span></span>
      </div>
    </div>

    <div class="btn-cta">{cta} 🚀</div>
    <div class="trust-strip">
      <span>✓ LLP Registered</span>
      <span>•</span>
      <span>✓ 0% Commission</span>
      <span>•</span>
      <span>✓ www.cafeqr.in</span>
      <span>•</span>
      <span>✓ Existing Hardware Compatible</span>
    </div>
  </div>
</body>
</html>"""
    return full_poster_html

