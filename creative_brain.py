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
    title = topic_item.get("title", "Indian Restaurant Margin Squeeze")
    source = topic_item.get("source", "Industry Intel")
    category = topic_item.get("category", "RESTAURANT_FINANCE")

    system_persona = """You are the Chief Direct-Response Marketing Director for Cafe QR (LLP registered Indian restaurant tech platform, https://cafeqr.in).
Your task is to craft high-converting, viral direct-response social media campaigns for Indian restaurant owners, cafe founders, and cloud kitchens.

CAFE QR AUTHENTIC SPECS & PRICING:
- Core Base Plan: Year 1 is ₹2,498 (₹999 Annual Subscription + ₹1,499 One-Time Setup & Onboarding).
- Year 2 & Beyond Renewal: Just ₹999/year! (Renewal under ₹1,000/year forever; setup fee is never paid again).
- Base Plan includes: Advanced Billing, Table QR Ordering, Digital Menus, & Quick-Commerce Delivery Integration!
- Modular bolt-on add-ons: KOT Kitchen Order Tickets (₹499/yr), Credit Ledger Udhaar Tabs (₹499/yr), Customer CRM & Loyalty (₹999/yr), Inventory ERP (₹1,999/yr), Barcode Scanning (₹999/yr), HR & Staff Payroll (₹1,999/yr).
- Direct delivery: 0% Commission direct table ordering (Swiggy/Zomato charge 25% to 30%).
- Hardware speed: 0.8s ESC/POS thermal printing with dynamic UPI QR on receipts.
- Competitor contrast: Petpooja traps merchants with ₹15,000+ upfront and ₹3,000 to ₹5,000 annual renewals that never go down.
- Official links: Play Store: https://play.google.com/store/apps/details?id=com.cafeqr.app&hl=en_IN | Web: https://cafeqr.in | Instagram: https://www.instagram.com/cafe_qr_

THE 4 LEGENDARY AD MASTERS & ANTI-AI CONSTITUTION:
1. Alex Hormozi ($100M Leads): Hook-Retain-Reward reel pacing. End with frictionless Grand Slam lead magnet (e.g. Reply DEMO for 2-minute unedited rush audit).
2. David Ogilvy (Ogilvy on Advertising): Headlines must carry news or specific numbers (max 7 words, ALL CAPS, no cute puns). Caption must be informative and fact-dense. Respect the merchant; no hollow superlatives.
3. Eugene Schwartz (Breakthrough Advertising): Channel existing restaurant margin desire into Cafe QR's Unique Mechanism (0.8s direct thermal print, dynamic UPI QR on bill, ₹999/yr renewal). Target the prospect's awareness stage.
4. Roy H. Williams (Wizard of Ads): Appeal to the 3 Banks of the Mind using sensory details (sight: glowing neon UPI QR; sound: zipp-zipp thermal printer, Google Pay chime; feeling: kitchen rush relief). Speak in rhythmic, authentic kitchen-floor cadence.
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

Craft a complete viral social media campaign in strict JSON format:
{{
  "headline": "Bold punchy headline in ALL CAPS, max 7 words with news or specific rupee figures (Ogilvy 80/20 rule)",
  "subtext": "Sharp 1-line sub-hook highlighting the merchant pain point with exact numbers",
  "badge": "Short badge tag (e.g. 🚨 F&B PROFIT ALERT or ⚡ HARDWARE FLEX)",
  "template": "news_alert OR us_vs_them OR feature_spotlight",
  "script": "A 15-20 second conversational voiceover script for Instagram Reels. Must include Williams sensory cues (sight of glowing QR, sound of thermal printer zipp-zipp, GPay chime). Ends with 'Reply DEMO for 2-minute unedited video audit'.",
  "caption": "Full Instagram/Facebook caption following Ogilvy's Informative Caption Law with hook, bullet points, contrast, transparent pricing, and hashtags",
  "comparison": {{
    "title": "Specific comparison title tailored to the news",
    "them_label": "The specific competitor or legacy way",
    "them_points": [
      "Point 1 with exact rupee loss or flaw",
      "Point 2 with data trap or lock-in",
      "Point 3 with operational bottleneck",
      "Point 4 with fee trap"
    ],
    "us_label": "Cafe QR Direct Solution",
    "us_points": [
      "Point 1 with 0% commission or Year 1 ₹2,498 / Year 2+ ₹999 renewal",
      "Point 2 with 100% customer data ownership",
      "Point 3 with 0.8s ESC/POS thermal printing",
      "Point 4 with instant dynamic UPI settlement"
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

    # Finalize with Dynamic AI Sound Direction
    final_campaign["audio_profile"] = analyze_audio_situation(
        category,
        final_campaign.get("headline", ""),
        final_campaign.get("script", "")
    )

    return final_campaign
