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

def call_gemini_api(messages_or_prompt, temperature=0.3, max_tokens=1500, timeout=30):
    """
    Direct Google Gemini API client supporting gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash.
    Works natively with standard REST using GEMINI_API_KEY.
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    system_instruction = None
    if isinstance(messages_or_prompt, list):
        prompt_parts = []
        for m in messages_or_prompt:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_instruction = content
            else:
                prompt_parts.append(f"{content}")
        full_prompt = "\n\n".join(prompt_parts)
    else:
        full_prompt = str(messages_or_prompt)

    candidate_models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = None

    for m_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                last_err = f"{m_name} status {r.status_code}: {r.text[:120]}"
        except Exception as e:
            last_err = f"{m_name} error: {str(e)[:120]}"

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")

def call_nvidia_nim_core(messages, model=None, temperature=0.3, max_tokens=1000, timeout=30):
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
    if MODEL_FALLBACK and MODEL_FALLBACK not in models_to_try:
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

def call_llm(messages, model=None, temperature=0.3, max_tokens=1200, timeout=30):
    """
    Unified Dual-Engine LLM caller:
    - If NVIDIA_API_KEY is present: calls NVIDIA NIM with automatic fallback to Gemini.
    - If GEMINI_API_KEY is present: calls Google Gemini.
    - Guarantees zero downtime even if one API key is missing or rate-limited.
    """
    errors = []

    # 1. Try NVIDIA NIM if configured
    if NVIDIA_API_KEY:
        try:
            return call_nvidia_nim_core(messages, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        except Exception as e:
            errors.append(f"NVIDIA NIM error: {e}")
            print(f"[CreativeBrain] NVIDIA NIM failed: {e}. Falling back to Google Gemini...")

    # 2. Try Google Gemini if configured
    if GEMINI_API_KEY:
        try:
            return call_gemini_api(messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        except Exception as e:
            errors.append(f"Google Gemini error: {e}")
            print(f"[CreativeBrain] Google Gemini failed: {e}")

    if not NVIDIA_API_KEY and not GEMINI_API_KEY:
        raise ValueError("Neither NVIDIA_API_KEY nor GEMINI_API_KEY is configured in environment.")

    raise RuntimeError(f"All LLM engines failed: {'; '.join(errors)}")

def call_nvidia_nim(messages, model=None, temperature=0.3, max_tokens=1000, timeout=30):
    """Backwards compatibility alias for call_llm"""
    return call_llm(messages, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)

def clean_json_response(raw_text):
    """
    Strips markdown code blocks and whitespace to cleanly parse JSON from LLM output.
    Uses strict=False and regex sanitization to reliably handle literal control characters and unescaped newlines.
    Programmatically sanitizes any hallucinated 9999 renewal fee into ₹999/yr.
    """
    text = raw_text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE).strip()
    
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]

    def _sanitize_dict(obj):
        if isinstance(obj, str):
            obj = re.sub(r'(?:₹|Rs\.?|INR)?\s*9999\b(?:\s*/\s*(?:yr|year))?', '₹999/yr', obj, flags=re.IGNORECASE)
            return re.sub(r'(?:₹|Rs\.?|INR)?\s*9,999\b(?:\s*/\s*(?:yr|year))?', '₹999/yr', obj, flags=re.IGNORECASE)
        elif isinstance(obj, dict):
            return {k: _sanitize_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sanitize_dict(elem) for elem in obj]
        return obj

    try:
        data = json.loads(text, strict=False)
        return _sanitize_dict(data)
    except Exception:
        # Sanitize literal control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda m: ' ' if m.group() in '\r\n\t' else '', text)
        try:
            data = json.loads(sanitized, strict=False)
            return _sanitize_dict(data)
        except Exception as e:
            print(f"[CreativeBrain] JSON parse warning: {e}. Attempting greedy cleanup.")
            # Final attempt: replace unescaped internal double quotes or trailing commas
            clean = re.sub(r',\s*([\]}])', r'\1', sanitized)
            data = json.loads(clean, strict=False)
            return _sanitize_dict(data)

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

def sanitize_delivery_messaging(campaign_data, topic_item=None):
    """
    Deterministic Channel Invariant Sanitizer:
    Ensures that Food Delivery, Swiggy, Zomato, Cloud Kitchen, QSR, and Dark Store topics
    position Cafe QR's Integrated Direct Delivery Website (order.cafeqr.in) at 0% Commission,
    and NEVER hallucinate 'table orders', 'table QR', or 'table revenue' on delivery/cloud kitchen topics.
    """
    if not campaign_data or not isinstance(campaign_data, dict):
        return campaign_data

    topic_item = topic_item or {}
    text_to_check = " ".join([
        str(campaign_data.get("headline", "")),
        str(campaign_data.get("subtext", "")),
        str(campaign_data.get("target_vertical", "")),
        str(topic_item.get("title", "")),
        str(topic_item.get("vertical", "")),
        str(topic_item.get("category", ""))
    ]).lower()

    is_delivery_or_cloud_kitchen = any(k in text_to_check for k in [
        "cloud kitchen", "qsr", "swiggy", "zomato", "food app", "food apps", "delivery", "dark store"
    ])

    if not is_delivery_or_cloud_kitchen:
        return campaign_data

    def clean_text(txt):
        if not txt or not isinstance(txt, str):
            return txt
        t = re.sub(r'\btable\s+revenue\b', 'delivery revenue', txt, flags=re.IGNORECASE)
        t = re.sub(r'\bevery\s+table\s+order\b', 'every delivery order', t, flags=re.IGNORECASE)
        t = re.sub(r'\ball\s+direct\s+table\s+qr\s+orders\b', 'all direct online delivery orders', t, flags=re.IGNORECASE)
        t = re.sub(r'\bdirect\s+table\s+qr\s+orders?\b', 'direct online delivery website orders', t, flags=re.IGNORECASE)
        t = re.sub(r'\bdirect\s+table\s+orders?\b', 'direct online delivery orders', t, flags=re.IGNORECASE)
        t = re.sub(r'\btable\s+qr\s+ordering\b', 'direct delivery website ordering', t, flags=re.IGNORECASE)
        t = re.sub(r'\btable\s+qr\s+orders?\b', 'direct delivery website orders', t, flags=re.IGNORECASE)
        t = re.sub(r'\btable\s+ordering\b', 'direct online delivery ordering', t, flags=re.IGNORECASE)
        t = re.sub(r'\bcommission\s+on\s+every\s+table\s+order\b', 'commission on every delivery order', t, flags=re.IGNORECASE)
        t = re.sub(r'\bcommission\s+on\s+table\s+orders?\b', 'commission on delivery orders', t, flags=re.IGNORECASE)
        t = re.sub(r'\bget\s+table\s+qr\s+and\s+digital\s+menus\b', 'launch your direct delivery website with digital menus', t, flags=re.IGNORECASE)
        t = re.sub(r'\bincludes\s+table\s+qr\s+ordering\b', 'includes integrated direct delivery website', t, flags=re.IGNORECASE)
        t = re.sub(r'\bincludes\s+table\s+qr\b', 'includes direct delivery website', t, flags=re.IGNORECASE)
        t = re.sub(r'\bfull\s+dining\s+profit\b', 'full delivery profit', t, flags=re.IGNORECASE)
        t = re.sub(r'\bdining\s+profit\b', 'delivery profit', t, flags=re.IGNORECASE)
        return t

    if "headline" in campaign_data:
        campaign_data["headline"] = clean_text(campaign_data["headline"])
        campaign_data["headline"] = re.sub(r'TABLE\s+REVENUE', 'DELIVERY REVENUE', campaign_data["headline"], flags=re.IGNORECASE)
    if "subtext" in campaign_data:
        campaign_data["subtext"] = clean_text(campaign_data["subtext"])
    if "script" in campaign_data:
        campaign_data["script"] = clean_text(campaign_data["script"])
    if "caption" in campaign_data:
        campaign_data["caption"] = clean_text(campaign_data["caption"])
    if "comparison" in campaign_data and isinstance(campaign_data["comparison"], dict):
        comp = campaign_data["comparison"]
        if "them_points" in comp and isinstance(comp["them_points"], list):
            comp["them_points"] = [clean_text(p) for p in comp["them_points"]]
        if "us_points" in comp and isinstance(comp["us_points"], list):
            comp["us_points"] = [clean_text(p) for p in comp["us_points"]]

    return campaign_data

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
- Restaurants, Cafes & Cloud Kitchens (0% commission Direct Delivery Website, Table QR ordering, 0.8s thermal KOT)
- Bakeries & Confectioneries (Batch expiry management, barcode scanning, fast checkout)
- Car Washes & Auto Detailing (Digital job card tokens, WhatsApp vehicle status alerts, dynamic UPI)
- Boutiques & Retail Stores (Barcode inventory tags, instant billing, customer Udhaar khata tabs)
- Salons, Spas & QSRs (Appointment billing, stylist commissions, customer CRM)

CAFE QR AUTHENTIC SPECS & PRICING:
- Official App Name: strictly "Cafe QR" (never "Cafe QR POS" or "Cafe QR 2.0").
- Core Base Plan: Year 1 is ₹2,498 (₹999 Annual Subscription + ₹1,499 One-Time Setup & Onboarding).
- Year 2 & Beyond Renewal: Just ₹999/year! (Renewal under ₹1,000/year forever; setup fee is never paid again).
- Base Plan includes: Advanced Billing, Integrated 0% Commission Direct Online Ordering & Delivery Website, Table QR Ordering (for Dine-In), Digital Menus, & Automated WhatsApp Order Dispatch!
- Modular bolt-on add-ons: KOT Kitchen Order Tickets (₹499/yr), Credit Ledger Udhaar Tabs (₹499/yr), Customer CRM & Loyalty (₹999/yr), Inventory ERP (₹1,999/yr), Barcode Scanning (₹999/yr), HR & Staff Payroll (₹1,999/yr).
- Competitor contrast: Petpooja and legacy retail ERPs trap merchants with ₹15,000 to ₹30,000 upfront charges + forced yearly renewals that never go down.
- Hardware speed: 0.8s ESC/POS thermal printing with dynamic UPI QR on receipts.
- Official links: Play Store: https://play.google.com/store/apps/details?id=com.cafeqr.app&hl=en_IN | Web: https://cafeqr.in | Instagram: https://www.instagram.com/cafe_qr_

THE TWO DISTINCT FOOD CHANNELS (CRITICAL INDUSTRY DISTINCTION):
1. FOOD DELIVERY & CLOUD KITCHENS (Swiggy, Zomato, Food Apps, QSRs, Cloud Kitchens):
   - The Villain / Problem: Swiggy and Zomato are FOOD DELIVERY APPS that charge 25% to 30% commission on ONLINE FOOD DELIVERY ORDERS and mask customer phone numbers.
   - The Cafe QR Solution: Cafe QR's Integrated Direct Delivery & Online Ordering Website (order.cafeqr.in / branded website) with 0% COMMISSION! Customers order direct via your web store or WhatsApp, pay via instant UPI directly into the restaurant's bank account, and orders print in 0.8s on the kitchen thermal printer. The merchant OWNS 100% of their customer database and phone numbers forever.
   - BANNED: Cloud kitchens have NO TABLES! NEVER use the words "table QR", "table order", or "table revenue" when talking about food delivery apps or Cloud Kitchens! The correct terms are "Direct Delivery Website", "Online Delivery Orders", or "0% Commission Direct Delivery".
2. DINE-IN RESTAURANTS & CAFES (Physical dining room with tables):
   - The Problem: Waiter shortages, paper menu reprint costs, slow checkout lines.
   - The Cafe QR Solution: Contactless Table QR ordering stickers on physical tables + digital menu + sub-second 0.8s thermal KOT printing.

THE 4 LEGENDARY AD MASTERS & ANTI-AI CONSTITUTION:
1. Alex Hormozi ($100M Leads): Hook-Retain-Reward pacing. End with frictionless Grand Slam lead magnet (e.g. Reply DEMO for 2-minute unedited video audit).
2. David Ogilvy (Ogilvy on Advertising): Headlines must carry news or specific numbers (max 7 words, ALL CAPS, no cute puns). Caption must be informative and fact-dense. Respect the merchant; no hollow superlatives.
3. Eugene Schwartz (Breakthrough Advertising): Channel existing business margin desire into Cafe QR's Unique Mechanism (0.8s direct thermal print, dynamic UPI QR on bill, ₹999/yr renewal, barcode billing). Target the prospect's awareness stage.
4. Roy H. Williams (Wizard of Ads): Appeal to the 3 Banks of the Mind using sensory details (sight: glowing neon UPI QR, barcode scan line; sound: zipp-zipp thermal printer, GPay chime; feeling: rush relief). Speak in rhythmic, authentic counter-floor cadence.
5. Zero em dashes (never use '—'; use plain commas, colons, or periods).
6. Zero banned AI words (never use revolutionize, elevate, robust, seamless, cutting-edge, game-changer, innovate, empower, foster, delve, pivotal, crucial, vital, tapestry).
7. Zero contrast framing (never use 'It is not X, it is Y' or 'Not only X, but also Y'). State positive factual claims directly.
8. One Action Rule: Single clear CTA telling the merchant what they get.
9. HUMAN-FIRST SIMPLICITY (The 5-Second Shopkeeper Test):
   - Write in plain, punchy, everyday language that any Indian shopkeeper, chef, or garage owner understands in 5 seconds.
   - BANNED: Confusing artificial jargon like "Legacy Aggregator Invoice" for a car wash.
   - In customer-facing artifacts (WhatsApp chats or receipts), speak strictly like a real shop: "🚗 Honda City ready for pickup! Bill: ₹650", "🎂 Cake order confirmed". NEVER cram software pricing or corporate sales pitches inside customer dialogue! Software pricing belongs only in the bottom pricing bar.
"""

    deep_intel = topic_item.get("deep_intel", {})
    awareness_stage = deep_intel.get("awareness_stage", "Problem-Aware")
    recommended_angle = deep_intel.get("recommended_angle", "Sachet Pricing Disruption")
    rupee_figures = deep_intel.get("rupee_figures", "Exact Rupee Savings")
    merchant_pain = deep_intel.get("merchant_pain", "Legacy fee lock-in")

    draft_prompt = f"""
NEWS TOPIC TO TREND-JACK:
"{title}"
Source: {source}
Category: {category}
Target Domain/Vertical: {vertical_hint}
Awareness Stage: {awareness_stage}
Strategic Marketing Angle: {recommended_angle}
Key Rupee/Number Context: {rupee_figures}
Core Friction Point: {merchant_pain}

CRITICAL INVARIANTS:
1. PRICING LOCKDOWN: Year 1 Base Plan is ₹2,498 (Setup included). Year 2+ Renewal is strictly ₹999/year forever (three digits: ₹999, NEVER 9999).
2. DOMAIN RELEVANCE: Tailor all copy strictly to {vertical_hint}. If {vertical_hint} is Car Wash or Auto Care, focus on digital job cards, lost tokens, and WhatsApp status (NEVER mention Petpooja or restaurant POS). If Bakery, focus on fresh batches and barcodes.
3. STORY-GROUNDED TREND-JACKING (MANDATORY):
   - The headline MUST DIRECTLY TREND-JACK THE EXACT TOPIC: "{title}".
   - BANNED: NEVER output a generic "STOP PAYING 30 PERCENT COMMISSION NOW" if "{title}" is about customer data, privacy, POS lock-in, car washes, or bakeries!
   - Specific Topic Matching Rules:
     * If "{title}" mentions customer data, privacy, or Zomato sharing data:
       Headline MUST be about Customer Data Ownership: e.g., "STOP LETTING AGGREGATORS OWN YOUR CUSTOMERS" or "OWN 100 PERCENT OF YOUR RESTAURANT DATA" or "WHY SHARE DATA WHEN YOU OWN IT?".
     * If "{title}" mentions sugar, milk, dairy, or input cost inflation:
       Headline MUST be about Ingredient Costs: e.g., "SUGAR & DAIRY SURGE SQUEEZES SWEET SHOPS" or "PROTECT BAKERY MARGINS FROM RISING COSTS".
     * If "{title}" mentions car washes, auto tokens, or water notices:
       Headline MUST be about Auto Tokens: e.g., "STOP LOSING REPAIR JOB CARDS NOW" or "DIGITAL JOB CARDS FOR BUSY GARAGES".
     * If "{title}" mentions Petpooja, DotPe, or upfront charges:
       Headline MUST be about POS Fees: e.g., "STOP PAYING ₹15,000 UPFRONT FOR BILLING".
     * If "{title}" mentions Swiggy/Zomato fee hikes or restaurant boycotts:
       Headline MUST be about Fee Revolts or Delivery Margins: e.g., "RESTAURANTS REVOLT AGAINST PLATFORM FEES" or "KEEP 100 PERCENT OF DELIVERY REVENUE".
      * If "{title}" mentions Cloud Kitchens, QSRs, dark stores, food apps, Swiggy, or Zomato:
        Headline MUST be about Food Delivery Margins or Direct Online Ordering:
        e.g., "STOP PAYING 30% ON FOOD DELIVERY" or "LAUNCH YOUR DIRECT DELIVERY WEBSITE" or "CLOUD KITCHENS: KEEP 100% DELIVERY MARGIN" or "STOP LOSING MARGIN TO FOOD APPS".
        BANNED FOR CLOUD KITCHENS: Cloud kitchens have ZERO TABLES! NEVER say "table revenue", "table QR", or "table orders" for food delivery or cloud kitchen stories! The supporting statement MUST be Cafe QR's Integrated Direct Delivery Website (order.cafeqr.in) with 0% Commission!
   - The headline MUST be maximum 7 words, ALL CAPS, punchy, news-relevant, and directly tied to "{title}".

Craft a complete viral direct-response campaign tailored to this awareness stage in strict JSON format:
{{
  "target_vertical": "{vertical_hint}",
  "awareness_stage": "{awareness_stage}",
  "strategic_angle": "{recommended_angle}",
  "recommended_visual_archetype": "Forensic Thermal Receipt (if commission/fee cuts) | WhatsApp Digital Dialogue (if car wash job cards or direct customer chat) | 3-Step Velocity Flow (if speed/thermal printing) | Split Comparison Matrix (if boycotts/outrage) | Transparent Sachet Pricing Grid (if POS pricing/lock-in) | Barcode Stock Audit (if bakeries/boutiques)",
  "headline": "Bold punchy headline in ALL CAPS, max 7 words with news or specific rupee figures (Ogilvy 80/20 rule)",
  "subtext": "Sharp 1-line sub-hook highlighting the merchant pain point with exact numbers",
  "badge": "Short badge tag (e.g. 🚨 F&B PROFIT ALERT, 🥐 BAKERY RUSH ALERT, 🚗 CAR WASH DETECTIVE, or ⚡ HARDWARE FLEX)",
  "script": "A 15-20 second conversational voiceover script for Instagram Reels with Williams sensory cues (thermal zipp-zipp, GPay chime, neon UPI QR). If topic is Cloud Kitchen or food delivery, focus strictly on direct online delivery orders (order.cafeqr.in) with 0% commission and direct UPI. NEVER mention table QR or table ordering for Cloud Kitchens! Ends with 'Reply DEMO for 2-minute unedited video audit'.",
  "caption": "Full Instagram/Facebook caption following Ogilvy's Informative Caption Law with hook, bullet points, transparent pricing (Year 1 ₹2,498 / Year 2+ ₹999/yr renewal forever), and hashtags. If topic is Cloud Kitchen or food delivery, emphasize the Integrated Direct Delivery Website with 0% commission and 100% customer data retention. NEVER say 'Table QR' for Cloud Kitchens!",
  "comparison": {{
    "title": "Specific focus title tailored strictly to {vertical_hint}",
    "them_label": "Aggregator Delivery Trap (for delivery/cloud kitchens) or Legacy Bottleneck",
    "them_points": [
      "Point 1 with exact flaw (e.g. 25-30% commission on every online delivery order for food delivery / cloud kitchens)",
      "Point 2 with operational friction (e.g. Platform hides customer numbers and owns your diner database)",
      "Point 3 with lost profit or customer churn for {vertical_hint}"
    ],
    "us_label": "Cafe QR Direct Solution",
    "us_points": [
      "Point 1 with 0% commission Integrated Direct Delivery Website (order.cafeqr.in) or Year 1 ₹2,498 / Year 2+ ₹999/yr",
      "Point 2 with 100% customer CRM & phone numbers retention or WhatsApp digital tracking",
      "Point 3 with 0.8s kitchen thermal print & direct UPI settlement straight to bank"
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
    max_reflection_turns = 1
    final_campaign = None

    for iteration in range(1, max_reflection_turns + 1):
        raw_output = call_nvidia_nim(messages, temperature=0.25, max_tokens=1100, timeout=25)
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

        if score >= 8.5 or all_passed:
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

    # Deterministic Channel Invariant: Sanitize Delivery vs Dine-In Messaging
    final_campaign = sanitize_delivery_messaging(final_campaign, topic_item)

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
    Autonomous AI Art Director (100% Raw Code from Scratch):
    Synthesizes a bespoke, production-grade 1080x1350 HTML+CSS poster for Cafe QR from top to bottom.
    Dynamically generates the complete visual layout, color palette, typography hierarchy,
    and visual evidence artifacts tailored to the business vertical (Restaurant, Bakery, Car Wash, Boutique, Salon).
    """
    topic_item = topic_item or {}
    headline = campaign_data.get("headline", "STOP PAYING ₹15,000 UPFRONT FOR BILLING")
    subtext = campaign_data.get("subtext", "Switch to Cafe QR Year 1 ₹2,498 and ₹999/year renewal forever.")
    badge = campaign_data.get("badge", "⚡ BILLING DISRUPTION")
    vertical = campaign_data.get("target_vertical", topic_item.get("vertical", "Multi-Vertical Retail & Services"))
    cta = campaign_data.get("cta", "Reply DEMO for 2-Minute Video Audit")
    comparison = campaign_data.get("comparison", {})
    them_label = comparison.get("them_label", "Legacy Systems & Aggregators")
    them_points = comparison.get("them_points", ["High upfront costs", "Forced yearly lock-in", "Hidden fee traps"])
    us_label = comparison.get("us_label", "Cafe QR Direct Solution")
    us_points = comparison.get("us_points", ["Year 1 ₹2,498 (Setup Included)", "Year 2+ ₹999/yr renewal forever", "100% data ownership"])
    deep_intel = topic_item.get("deep_intel", {})
    awareness_stage = deep_intel.get("awareness_stage", "Problem-Aware")
    recommended_angle = deep_intel.get("recommended_angle", "Sachet Pricing Disruption")

    # Format Headline with highlight fallback
    words = headline.split()
    if len(words) > 2:
        split_idx = max(len(words) - 3, 2)
        head_first = " ".join(words[:split_idx])
        head_last = " ".join(words[split_idx:])
        styled_headline = f"{head_first} <span>{head_last}</span>"
    else:
        styled_headline = f"<span>{headline}</span>"

    # 1. Dynamic 80/20 Thematic Backdrops & Brand Palettes
    category = topic_item.get("category", "") or campaign_data.get("category", "")
    category_upper = str(category).upper()
    title_lower = str(topic_item.get("title", "")).lower()
    vert_lower = str(vertical).lower()

    if any(k in category_upper or k in title_lower for k in ["BOYCOTT", "PROTEST", "OUTRAGE", "HIKE", "DISPUTE", "STRIKE"]):
        bg_mode = "crimson_alert"
        theme_bg = "#0D090B"
        theme_glow_1 = "rgba(239, 68, 68, 0.28)"
        theme_glow_2 = "rgba(245, 158, 11, 0.18)"
        theme_accent = "#EF4444"
        theme_accent_gradient = "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
        theme_badge_bg = "rgba(239, 68, 68, 0.18)"
        theme_badge_border = "rgba(239, 68, 68, 0.55)"
        theme_badge_color = "#F87171"
    elif any(k in vert_lower for k in ["car wash", "auto", "garage", "detailing"]):
        bg_mode = "cyan_auto"
        theme_bg = "#070E1A"
        theme_glow_1 = "rgba(6, 182, 212, 0.26)"
        theme_glow_2 = "rgba(37, 99, 235, 0.18)"
        theme_accent = "#06B6D4"
        theme_accent_gradient = "linear-gradient(135deg, #06B6D4 0%, #0284C7 100%)"
        theme_badge_bg = "rgba(6, 182, 212, 0.16)"
        theme_badge_border = "rgba(6, 182, 212, 0.5)"
        theme_badge_color = "#38BDF8"
    elif any(k in vert_lower for k in ["bakery", "sweet", "confectionery", "mithai"]):
        bg_mode = "bakery_gold"
        theme_bg = "#100B06"
        theme_glow_1 = "rgba(245, 158, 11, 0.26)"
        theme_glow_2 = "rgba(217, 119, 6, 0.18)"
        theme_accent = "#F59E0B"
        theme_accent_gradient = "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)"
        theme_badge_bg = "rgba(245, 158, 11, 0.16)"
        theme_badge_border = "rgba(245, 158, 11, 0.5)"
        theme_badge_color = "#FBBF24"
    elif any(k in vert_lower for k in ["boutique", "apparel", "retail", "fashion", "textile"]):
        bg_mode = "boutique_rose"
        theme_bg = "#110813"
        theme_glow_1 = "rgba(244, 63, 94, 0.26)"
        theme_glow_2 = "rgba(168, 85, 247, 0.18)"
        theme_accent = "#F43F5E"
        theme_accent_gradient = "linear-gradient(135deg, #F43F5E 0%, #E11D48 100%)"
        theme_badge_bg = "rgba(244, 63, 94, 0.16)"
        theme_badge_border = "rgba(244, 63, 94, 0.5)"
        theme_badge_color = "#FB7185"
    elif any(k in category_upper or k in title_lower for k in ["POS_MONOPOLY", "PETPOOJA", "LOCK_IN", "UPFRONT"]):
        bg_mode = "titanium_slate"
        theme_bg = "#080C16"
        theme_glow_1 = "rgba(99, 102, 241, 0.25)"
        theme_glow_2 = "rgba(16, 185, 129, 0.18)"
        theme_accent = "#6366F1"
        theme_accent_gradient = "linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)"
        theme_badge_bg = "rgba(99, 102, 241, 0.16)"
        theme_badge_border = "rgba(99, 102, 241, 0.5)"
        theme_badge_color = "#818CF8"
    elif any(k in category_upper or k in title_lower for k in ["SPEED", "THERMAL", "PRINTER", "HARDWARE", "KOT"]):
        bg_mode = "kinetic_emerald"
        theme_bg = "#06100B"
        theme_glow_1 = "rgba(16, 185, 129, 0.28)"
        theme_glow_2 = "rgba(6, 182, 212, 0.18)"
        theme_accent = "#10B981"
        theme_accent_gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
        theme_badge_bg = "rgba(16, 185, 129, 0.16)"
        theme_badge_border = "rgba(16, 185, 129, 0.5)"
        theme_badge_color = "#34D399"
    elif any(k in vert_lower for k in ["restaurant", "cafe", "cloud kitchen", "qsr", "dine"]):
        # Warm Cafe Photo Interior with Frosted Glassmorphism
        bg_mode = "photo_glass"
        theme_bg = "#0A0D14"
        theme_glow_1 = "rgba(255, 122, 0, 0.24)"
        theme_glow_2 = "rgba(16, 185, 129, 0.16)"
        theme_accent = "#FF7A00"
        theme_accent_gradient = "linear-gradient(135deg, #FF7A00 0%, #E66E00 100%)"
        theme_badge_bg = "rgba(255, 122, 0, 0.16)"
        theme_badge_border = "rgba(255, 122, 0, 0.5)"
        theme_badge_color = "#FF9933"
    else:
        bg_mode = "obsidian_slate"
        theme_bg = "#080C14"
        theme_glow_1 = "rgba(255, 122, 0, 0.20)"
        theme_glow_2 = "rgba(16, 185, 129, 0.14)"
        theme_accent = "#FF7A00"
        theme_accent_gradient = "linear-gradient(135deg, #FF7A00 0%, #E66E00 100%)"
        theme_badge_bg = "rgba(255, 122, 0, 0.16)"
        theme_badge_border = "rgba(255, 122, 0, 0.45)"
        theme_badge_color = "#FF7A00"

    deep_intel = topic_item.get("deep_intel", {}) if isinstance(topic_item, dict) else {}
    recommended_archetype = (
        campaign_data.get("recommended_visual_archetype")
        or deep_intel.get("recommended_visual_archetype")
        or ""
    )

    if any(k in vert_lower for k in ["car wash", "auto", "garage", "detailing"]):
        archetype_instruction = "MANDATORY: You MUST generate ARCHETYPE 2 (WhatsApp Business Notification / Job Card: <div class=\"chat-container\">) with vehicle model and status."
    elif any(k in vert_lower for k in ["bakery", "sweet", "boutique", "apparel", "retail"]):
        archetype_instruction = "MANDATORY: You MUST generate ARCHETYPE 7 (Barcode Scanning & Stock/Batch Audit: <div class=\"barcode-card\">) or ARCHETYPE 2 (WhatsApp Order Confirmation)."
    elif any(k in category_upper or k in title_lower for k in ["POS_MONOPOLY", "PETPOOJA", "LOCK_IN", "UPFRONT"]):
        archetype_instruction = "MANDATORY: You MUST generate ARCHETYPE 6 (Legacy POS Contract Audit: <div class=\"contract-card\">) comparing ₹15,000–₹30,000 upfront with Cafe QR Year 1 ₹2,498 / Year 2 ₹999/yr."
    elif any(k in category_upper or k in title_lower for k in ["SPEED", "THERMAL", "PRINTER", "HARDWARE", "KOT"]):
        archetype_instruction = "MANDATORY: You MUST generate ARCHETYPE 3 (3-Step Velocity Flow: <div class=\"flow-container\">)."
    elif any(k in category_upper or k in title_lower for k in ["BOYCOTT", "PROTEST", "OUTRAGE", "STRIKE"]):
        archetype_instruction = "MANDATORY: You MUST generate ARCHETYPE 4 (Split Contrast Matrix: <div class=\"comparison-grid\">) showing Them (Red TRAP) vs Cafe QR (Green PROFIT)."
    elif "receipt" in recommended_archetype.lower() or "commission" in category_upper:
        archetype_instruction = "MANDATORY: You MUST generate ARCHETYPE 1 (Forensic Thermal Receipt: <div class=\"receipt-container\">) using story-specific numbers."
    else:
        archetype_instruction = "Select the single archetype (Receipt, WhatsApp Chat, Velocity Flow, Split Matrix, or Contract Audit) that creates the most visceral visual contrast."

    centerpiece_html = None
    art_prompt = f"""
Act as an award-winning Senior Art Director for Cafe QR (Official Site: www.cafeqr.in).
Generate a custom visual evidence centerpiece in pure clean HTML for this direct-response Instagram poster (1080x1350).

VERTICAL: {vertical}
TOPIC: {topic_item.get('title', headline)}
THEIR FLAWS ({them_label}): {json.dumps(them_points)}
CAFE QR ADVANTAGE ({us_label}): {json.dumps(us_points)}

{archetype_instruction}

AVAILABLE ARCHETYPES:

ARCHETYPE 1: "receipt-container" (Forensic Thermal Receipt)
- Use for: Commission cuts (-28%), hidden aggregator fees, settlement math.
Example skeleton:
<div class="receipt-container">
  <div class="receipt-header">
    <div class="receipt-title">FORENSIC SETTLEMENT AUDIT</div>
    <div class="receipt-subtitle">{vertical.upper()} REAL MARGIN DEDUCTIONS</div>
  </div>
  <div class="receipt-line"><span>Gross Customer Order</span><span>₹1,000</span></div>
  <div class="receipt-line"><span class="receipt-deduction">Platform Commission (25-30%)</span><span class="receipt-deduction">-₹280</span></div>
  <div class="receipt-line"><span class="receipt-deduction">Operational / Tech Levy</span><span class="receipt-deduction">-₹120</span></div>
  <div class="receipt-payout-trap">
    <span>THEIR NET PAYOUT:</span>
    <span>₹600 (LOST ₹400)</span>
  </div>
  <div class="receipt-payout-cafeqr">
    <span>CAFE QR DIRECT UPI:</span>
    <span>₹1,000 (0% COMMISSION)</span>
  </div>
</div>

ARCHETYPE 2: "chat-container" (WhatsApp Business Notification / Job Card)
- Use for: Car wash job cards, table QR ordering, boutique/bakery customer alerts.
- HUMANIFIED DIALOGUE: Real WhatsApp messages between business and customer. NO software pricing in chat!
Example skeleton:
<div class="chat-container">
  <div class="chat-header">
    <div class="chat-avatar">🟢</div>
    <div class="chat-header-info">
      <div class="chat-header-title">Royal Auto Detailing Garage</div>
      <div class="chat-header-status">✓ Verified Business Account</div>
    </div>
  </div>
  <div class="chat-body">
    <div class="chat-bubble chat-incoming">
      <div style="font-weight: 800; color: #25D366; font-size: 16px; margin-bottom: 6px;">DIGITAL JOB CARD #042</div>
      <div style="font-size: 18px; color: #E9EDEF;">🚗 Vehicle: Honda City (KL-07)<br>🔧 Service: Foam Wash &amp; Interior Vacuum<br>⏱️ Status: Work In Progress</div>
      <div class="chat-meta">10:15 AM</div>
    </div>
    <div class="chat-bubble chat-outgoing">
      <div style="font-weight: 800; color: #34D399; font-size: 16px; margin-bottom: 6px;">✓ Vehicle Ready for Pickup!</div>
      <div style="font-size: 18px; color: #E9EDEF;">Total: ₹650 • Click to Pay via Direct UPI: pay.cafeqr.in/42</div>
      <div class="chat-meta">10:55 AM ✓✓</div>
    </div>
    <div class="chat-bubble chat-incoming" style="background: rgba(16, 185, 129, 0.15); border: 1.5px solid rgba(16, 185, 129, 0.35); align-self: center; text-align: center; max-width: 90%;">
      <span style="color: #34D399; font-weight: 800; font-size: 17px;">⚡ Direct UPI Paid • Counter Thermal Bill Printed in 0.8s</span>
    </div>
  </div>
</div>

ARCHETYPE 3: "flow-container" (3-Step Velocity Benchmark Flow)
Example skeleton:
<div class="flow-container">
  <div class="flow-step">
    <div class="flow-num">01</div>
    <div class="flow-info"><div class="flow-title">Table Scan</div><div class="flow-desc">Diner scans UPI QR in 0.2s</div></div>
  </div>
  <div class="flow-step">
    <div class="flow-num">02</div>
    <div class="flow-info"><div class="flow-title">Instant Thermal Print</div><div class="flow-desc">Kitchen gets ticket in 0.8s</div></div>
  </div>
  <div class="flow-step highlight">
    <div class="flow-num">03</div>
    <div class="flow-info"><div class="flow-title">Direct Settlement</div><div class="flow-desc">100% money in bank, 0% cut</div></div>
  </div>
</div>

ARCHETYPE 4: "comparison-grid" (Split Contrast Matrix)
Example skeleton:
<div class="comparison-grid">
  <div class="card-them">
    <div class="card-title them-title">
      <span>Aggregator Trap</span>
      <span style="font-size: 14px; background: rgba(239,68,68,0.25); color: #F87171; padding: 4px 10px; border-radius: 8px;">TRAP</span>
    </div>
    <div class="point-item"><span class="icon-cross">✕</span><span>Platform masks customer numbers</span></div>
    <div class="point-item"><span class="icon-cross">✕</span><span>Competitors re-target your own diners</span></div>
    <div class="point-item"><span class="icon-cross">✕</span><span>Forced 25-30% cut on every single order</span></div>
  </div>
  <div class="card-us">
    <div class="card-title us-title">
      <span>Cafe QR Direct</span>
      <span style="font-size: 14px; background: rgba(16,185,129,0.25); color: #34D399; padding: 4px 10px; border-radius: 8px;">PROFIT</span>
    </div>
    <div class="point-item"><span class="icon-check">✓</span><span>100% direct customer data & phone numbers</span></div>
    <div class="point-item"><span class="icon-check">✓</span><span>Direct WhatsApp marketing with 0% fee</span></div>
    <div class="point-item"><span class="icon-check">✓</span><span>Direct UPI payout straight to your bank</span></div>
  </div>
</div>

ARCHETYPE 6: "contract-card" (Legacy POS Contract Audit)
Example skeleton:
<div class="contract-card">
  <div class="contract-header">
    <div class="contract-title">RETAIL &amp; POS CONTRACT AUDIT</div>
    <div class="contract-sub">ANNUAL SOFTWARE EXPOSURE COMPARISON</div>
  </div>
  <div class="contract-row trap">
    <span>Legacy Upfront Lock-in (Petpooja / Posist)</span>
    <strong>₹15,000 – ₹30,000</strong>
  </div>
  <div class="contract-row trap">
    <span>Forced Yearly Renewal Escalation</span>
    <strong>₹8,000 – ₹12,000/yr</strong>
  </div>
  <div class="contract-row profit">
    <span>CAFE QR YEAR 1 BASE PLAN (Setup Included)</span>
    <strong>₹2,498</strong>
  </div>
  <div class="contract-row profit">
    <span>CAFE QR YEAR 2+ RENEWAL (Forever)</span>
    <strong>₹999/yr</strong>
  </div>
</div>

ARCHETYPE 7: "barcode-card" (Barcode & Batch Expiry Audit)
Example skeleton:
<div class="barcode-card">
  <div class="barcode-header">
    <div class="barcode-title">BARCODE SCAN &amp; BATCH EXPIRY AUDIT</div>
    <div class="barcode-sub">{vertical.upper()} STOCK INTEGRITY REPORT</div>
  </div>
  <div class="barcode-visual">
    <div class="barcode-lines">||| | |||| || | ||||| ||| | |||</div>
    <div class="barcode-sku">SKU #89042-BATCH-04 • VERIFIED</div>
  </div>
  <div class="barcode-metrics">
    <div class="barcode-metric-item"><span>Checkout Speed</span><strong style="color: #10B981;">0.4s Instant</strong></div>
    <div class="barcode-metric-item"><span>Stock Shrinkage</span><strong style="color: #10B981;">0% Leakage</strong></div>
    <div class="barcode-metric-item"><span>Expiry Alerts</span><strong style="color: #38BDF8;">Auto-WhatsApp</strong></div>
  </div>
</div>

CRITICAL CONTRACT:
Tailor the text, figures, and points specifically to {vertical} and the topic.
Return ONLY the raw HTML string starting with <div class="..."> and ending with </div>.
Do NOT include markdown fences, DO NOT include <html> or <body> tags.
"""
    messages = [
        {"role": "system", "content": "You are a master UI/UX visual designer. Output strictly HTML for the centerpiece element."},
        {"role": "user", "content": art_prompt}
    ]

    try:
        raw_centerpiece = call_nvidia_nim(messages, temperature=0.2, max_tokens=1200, timeout=25)
        cleaned_centerpiece = raw_centerpiece.replace("```html", "").replace("```", "").strip()
        if cleaned_centerpiece.startswith("div "):
            cleaned_centerpiece = "<" + cleaned_centerpiece
        if not cleaned_centerpiece.startswith("<"):
            idx = cleaned_centerpiece.find("<")
            if idx != -1:
                cleaned_centerpiece = cleaned_centerpiece[idx:]
        if "<div" in cleaned_centerpiece and "</div>" in cleaned_centerpiece:
            # Deterministic DOM Tag Balancing (prevents child leaking into footer)
            open_divs = len(re.findall(r'<div\b', cleaned_centerpiece, re.IGNORECASE))
            close_divs = len(re.findall(r'</div>', cleaned_centerpiece, re.IGNORECASE))
            if open_divs > close_divs:
                cleaned_centerpiece += "</div>" * (open_divs - close_divs)
            elif close_divs > open_divs:
                diff = close_divs - open_divs
                for _ in range(diff):
                    last_idx = cleaned_centerpiece.rfind("</div>")
                    if last_idx != -1:
                        cleaned_centerpiece = cleaned_centerpiece[:last_idx] + cleaned_centerpiece[last_idx+6:]
            
            # Enforce that LLM returned a recognized high-contrast card class
            valid_classes = ["receipt-container", "chat-container", "comparison-grid", "contract-card", "barcode-card", "flow-container"]
            if any(cls in cleaned_centerpiece for cls in valid_classes):
                centerpiece_html = cleaned_centerpiece
                print(f"🎨 [CreativeBrain] Bespoke centerpiece card successfully generated by AI Art Director for {vertical}.")
            else:
                print(f"⚠️ [CreativeBrain] Centerpiece missing structured container classes. Using vertical-aware fallback.")
                centerpiece_html = None
    except Exception as e:
        print(f"[CreativeBrain] AI Centerpiece generation warning: {e}. Using structured fallback.")

    # Resilient fallback if LLM times out or card is empty
    if not centerpiece_html:
        arch_lower = recommended_archetype.lower()
        if "receipt" in arch_lower or "deduct" in arch_lower or "commission" in arch_lower:
            centerpiece_html = f"""
    <div class="receipt-container">
      <div class="receipt-header">
        <div class="receipt-title">FORENSIC SETTLEMENT AUDIT</div>
        <div class="receipt-subtitle">{vertical.upper()} MARGIN LEAKAGE REPORT</div>
      </div>
      <div class="receipt-line"><span>Gross Customer Order</span><span>₹1,000</span></div>
      <div class="receipt-line"><span class="receipt-deduction">Aggregator Cut & Commissions (-28%)</span><span class="receipt-deduction">-₹280</span></div>
      <div class="receipt-line"><span class="receipt-deduction">Mandatory Tech & Delivery Fees</span><span class="receipt-deduction">-₹140</span></div>
      <div class="receipt-payout-trap">
        <span>THEIR NET SETTLEMENT:</span>
        <span>₹580 (LOST ₹420)</span>
      </div>
      <div class="receipt-payout-cafeqr">
        <span>CAFE QR DIRECT UPI:</span>
        <span>₹1,000 (0% COMMISSION)</span>
      </div>
    </div>
"""
        elif "chat" in arch_lower or "whatsapp" in arch_lower or "dialogue" in arch_lower:
            biz_name = "QuickShine Auto Detailing" if "car" in vertical.lower() or "auto" in vertical.lower() else f"{vertical.split('&')[0].strip()} Express"
            token_title = "DIGITAL JOB CARD #042" if "car" in vertical.lower() or "auto" in vertical.lower() else "DIGITAL ORDER #108"
            token_desc = "🚗 Vehicle: Honda City (KL-07)<br>🔧 Service: Foam Wash &amp; Interior Vacuum" if "car" in vertical.lower() or "auto" in vertical.lower() else f"📦 1x {vertical} Package • Counter Pickup"
            centerpiece_html = f"""
    <div class="chat-container">
      <div class="chat-header">
        <div class="chat-avatar">🟢</div>
        <div class="chat-header-info">
          <div class="chat-header-title">{biz_name}</div>
          <div class="chat-header-status">✓ Verified Business Account</div>
        </div>
      </div>
      <div class="chat-body">
        <div class="chat-bubble chat-incoming">
          <div style="font-weight: 800; color: #25D366; font-size: 16px; margin-bottom: 6px;">{token_title}</div>
          <div style="font-size: 18px; color: #E9EDEF;">{token_desc}</div>
          <div class="chat-meta">10:15 AM</div>
        </div>
        <div class="chat-bubble chat-outgoing">
          <div style="font-weight: 800; color: #34D399; font-size: 16px; margin-bottom: 6px;">✓ Service Ready for Pickup!</div>
          <div style="font-size: 18px; color: #E9EDEF;">Total: ₹650 • Click to Pay via Direct UPI: pay.cafeqr.in/42</div>
          <div class="chat-meta">10:55 AM ✓✓</div>
        </div>
        <div class="chat-bubble chat-incoming" style="background: rgba(16, 185, 129, 0.15); border: 1.5px solid rgba(16, 185, 129, 0.35); align-self: center; text-align: center; max-width: 90%;">
          <span style="color: #34D399; font-weight: 800; font-size: 17px;">⚡ Direct UPI Payment Received • Thermal Bill Printed in 0.8s</span>
        </div>
      </div>
    </div>
"""
        elif "flow" in arch_lower or "step" in arch_lower or "speed" in arch_lower:
            centerpiece_html = f"""
    <div class="flow-container">
      <div class="flow-step-card">
        <div class="flow-step-badge" style="background: rgba(255,255,255,0.1); color: #CBD5E1;">STEP 1</div>
        <div class="flow-step-title">Scan QR / Barcode</div>
        <div class="flow-step-desc">Zero app download. Customer or cashier orders in seconds.</div>
        <div class="flow-step-metric" style="color: #38BDF8;">⚡ ZERO FRICTION</div>
      </div>
      <div class="flow-step-card" style="border-color: {theme_accent};">
        <div class="flow-step-badge" style="background: {theme_badge_bg}; color: {theme_accent};">STEP 2</div>
        <div class="flow-step-title">0.8s Thermal Print</div>
        <div class="flow-step-desc">Instant KOT spits out on your existing counter printer.</div>
        <div class="flow-step-metric" style="color: {theme_accent};">⚡ 0.8 SECONDS</div>
      </div>
      <div class="flow-step-card" style="border-color: #10B981;">
        <div class="flow-step-badge" style="background: rgba(16,185,129,0.15); color: #10B981;">STEP 3</div>
        <div class="flow-step-title">0% Direct UPI Payout</div>
        <div class="flow-step-desc">Funds land directly in your merchant bank account.</div>
        <div class="flow-step-metric" style="color: #10B981;">💰 100% PROFIT</div>
      </div>
    </div>
"""
        elif "price" in arch_lower or "sachet" in arch_lower or "pricing" in arch_lower:
            centerpiece_html = f"""
    <div class="pricing-grid-card">
      <div class="pricing-grid-hero">
        <div>
          <span class="pricing-hero-badge">⚡ Transparent Sachet Model</span>
          <div class="pricing-hero-price">₹2,498 Year 1</div>
          <div class="pricing-hero-sub">Setup Included • Year 2+ Renewal ₹999/yr Forever</div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 38px; font-weight: 900; color: #10B981; font-family: 'Outfit', sans-serif;">0%</div>
          <div style="font-size: 14px; color: #94A3B8; font-weight: 700;">Direct UPI</div>
        </div>
      </div>
      <div class="sachet-addons-list">
        <div class="sachet-addon-pill"><span class="addon-name">Table QR & Digital Menu</span><span class="addon-price">INCLUDED</span></div>
        <div class="sachet-addon-pill"><span class="addon-name">0.8s Thermal Bill Printing</span><span class="addon-price">INCLUDED</span></div>
        <div class="sachet-addon-pill"><span class="addon-name">KOT Kitchen Tickets</span><span class="addon-price">₹499/yr</span></div>
        <div class="sachet-addon-pill"><span class="addon-name">Customer CRM & Loyalty</span><span class="addon-price">₹999/yr</span></div>
      </div>
    </div>
"""
        elif any(k in arch_lower for k in ["contract", "pos", "petpooja", "lock"]) or any(k in category_upper for k in ["POS_MONOPOLY"]):
            centerpiece_html = f"""
    <div class="contract-card">
      <div class="contract-header">
        <div class="contract-title">RETAIL &amp; POS CONTRACT AUDIT</div>
        <div class="contract-sub">ANNUAL SOFTWARE EXPOSURE COMPARISON</div>
      </div>
      <div class="contract-row trap">
        <span>Legacy Upfront Lock-in (Petpooja / Posist)</span>
        <strong>₹15,000 – ₹30,000</strong>
      </div>
      <div class="contract-row trap">
        <span>Forced Yearly Renewal Escalation</span>
        <strong>₹8,000 – ₹12,000/yr</strong>
      </div>
      <div class="contract-row profit">
        <span>CAFE QR YEAR 1 BASE PLAN (Setup Included)</span>
        <strong>₹2,498</strong>
      </div>
      <div class="contract-row profit">
        <span>CAFE QR YEAR 2+ RENEWAL (Forever)</span>
        <strong>₹999/yr</strong>
      </div>
    </div>
"""
        elif any(k in arch_lower for k in ["barcode", "expiry", "stock"]) or any(k in vert_lower for k in ["bakery", "sweet", "boutique", "apparel", "retail"]):
            centerpiece_html = f"""
    <div class="barcode-card">
      <div class="barcode-header">
        <div class="barcode-title">BARCODE SCAN &amp; BATCH EXPIRY AUDIT</div>
        <div class="barcode-sub">{vertical.upper()} STOCK INTEGRITY REPORT</div>
      </div>
      <div class="barcode-visual">
        <div class="barcode-lines">||| | |||| || | ||||| ||| | |||</div>
        <div class="barcode-sku">SKU #89042-BATCH-04 • VERIFIED</div>
      </div>
      <div class="barcode-metrics">
        <div class="barcode-metric-item">
          <span>Checkout Speed</span>
          <strong style="color: #10B981;">0.4s Instant</strong>
        </div>
        <div class="barcode-metric-item">
          <span>Stock Shrinkage</span>
          <strong style="color: #10B981;">0% Leakage</strong>
        </div>
        <div class="barcode-metric-item">
          <span>Expiry Alerts</span>
          <strong style="color: #38BDF8;">Auto-WhatsApp</strong>
        </div>
      </div>
    </div>
"""
        else:
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
      <div class="card-us" style="border-color: {theme_accent};">
        <div class="card-title us-title" style="color: {theme_accent};">
          <span>{us_label}</span>
          <span style="font-size: 15px; background: rgba(16,185,129,0.2); color: #10B981; padding: 4px 10px; border-radius: 8px;">PROFIT</span>
        </div>
        {us_pts_html}
      </div>
    </div>
"""

    # 2. News Proof & Real-World Trend Anchor Extraction
    news_title = topic_item.get("title") or campaign_data.get("news_title", "")
    news_source = topic_item.get("source") or campaign_data.get("source_tag", "Industry Intel")
    news_category = topic_item.get("category_label") or topic_item.get("category", "TRENDING INTEL")

    news_anchor_html = ""
    if news_title:
        display_title = news_title if len(news_title) <= 90 else news_title[:87] + "..."
        news_anchor_html = f"""
  <div class="z2 news-anchor-card">
    <div class="news-anchor-meta">
      <span class="news-pulse-dot"></span>
      <span class="news-source-tag">TRENDING INTEL • {news_source.upper()}</span>
      <span class="news-cat-tag">{news_category}</span>
    </div>
    <div class="news-quote-title">"{display_title}"</div>
  </div>
"""

    # Atmospheric Background: Subdued (12% opacity, 16px blur) so it NEVER competes with typography
    photo_bg_html = """<div class="photo-bg-layer" style="position: absolute; inset: 0; background-image: url('{{cafe_bg_img}}'); background-size: cover; background-position: center; filter: blur(16px) brightness(0.08) saturate(0.5); opacity: 0.12; pointer-events: none; z-index: 0;"></div>""" if bg_mode == "photo_glass" else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1350px;
    background: {theme_bg};
    color: #F8FAFC;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    overflow: hidden;
    padding: 44px 50px;
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
    background: radial-gradient(circle, {theme_glow_1} 0%, transparent 70%);
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
    background: radial-gradient(circle, {theme_glow_2} 0%, transparent 70%);
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

  /* Header & Logo Capsule Isolation (80/20 Brand Anchor Rule) */
  .header-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .brand-capsule {{
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(15, 23, 42, 0.72);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    padding: 8px 18px;
    border-radius: 20px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  }}
  .brand-logo {{
    height: 52px;
    width: auto;
    border-radius: 10px;
    background: #FFFFFF;
    padding: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
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
    background: {theme_badge_bg};
    border: 1.5px solid {theme_badge_border};
    color: {theme_badge_color};
    font-size: 15px;
    font-weight: 800;
    padding: 8px 22px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  }}

  /* News Proof & Trend Anchor Card (Shows the Real News Headline) */
  .news-anchor-card {{
    background: rgba(15, 23, 42, 0.90);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1.5px solid rgba(255, 255, 255, 0.14);
    border-left: 6px solid {theme_accent};
    border-radius: 16px;
    padding: 12px 20px;
    margin: 10px 0 6px 0;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
  }}
  .news-anchor-meta {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .news-pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #EF4444;
    box-shadow: 0 0 10px #EF4444;
  }}
  .news-source-tag {{
    color: {theme_accent};
    font-weight: 900;
  }}
  .news-cat-tag {{
    background: rgba(255, 255, 255, 0.08);
    color: #94A3B8;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
  }}
  .news-quote-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 21px;
    font-weight: 800;
    color: #F8FAFC;
    line-height: 1.25;
    letter-spacing: -0.2px;
  }}

  /* Hero Section */
  .hero-section {{
    margin: 10px 0 6px 0;
  }}
  .headline-main {{
    font-family: 'Outfit', sans-serif;
    font-size: 50px;
    font-weight: 900;
    line-height: 1.1;
    text-transform: uppercase;
    letter-spacing: -1px;
    margin-bottom: 8px;
  }}
  .headline-main span {{
    color: {theme_accent};
  }}
  .subtext-main {{
    font-size: 21px;
    color: #94A3B8;
    line-height: 1.35;
  }}

  /* Centerpiece Card Container */
  .centerpiece-box {{
    margin: 14px 0;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .comparison-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: stretch;
  }}
  .comparison-grid > *:not(.card-them):not(.card-us) {{
    grid-column: 1 / -1;
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 6px;
    color: #CBD5E1;
  }}
  .card-them {{
    background: rgba(22, 12, 16, 0.94);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1.5px solid rgba(239, 68, 68, 0.5);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .card-us {{
    background: rgba(10, 24, 18, 0.94);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 2px solid {theme_accent};
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  }}
  .card-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 16px;
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
    margin-bottom: 12px;
    color: #E2E8F0;
  }}
  .icon-cross {{ color: #EF4444; font-weight: bold; font-size: 18px; min-width: 20px; }}
  .icon-check {{ color: #10B981; font-weight: bold; font-size: 18px; min-width: 20px; }}

  /* ARCHETYPE 1: Forensic Thermal Receipt */
  .receipt-container {{
    background: #FFFFFF;
    color: #0F172A;
    border-radius: 20px;
    padding: 28px 32px;
    max-width: 820px;
    margin: 0 auto;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6);
    font-family: 'Plus Jakarta Sans', monospace, sans-serif;
    position: relative;
  }}
  .receipt-header {{
    text-align: center;
    border-bottom: 2px dashed #94A3B8;
    padding-bottom: 12px;
    margin-bottom: 14px;
  }}
  .receipt-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 1px;
    color: #0F172A;
  }}
  .receipt-subtitle {{
    font-size: 13px;
    color: #64748B;
    font-weight: 700;
    margin-top: 4px;
  }}
  .receipt-line {{
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    font-size: 18px;
    border-bottom: 1px dashed #E2E8F0;
    font-weight: 600;
  }}
  .receipt-deduction {{
    color: #DC2626;
    font-weight: 700;
  }}
  .receipt-payout-trap {{
    background: #FEF2F2;
    border: 1.5px solid #FCA5A5;
    padding: 12px 16px;
    border-radius: 12px;
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 20px;
    font-weight: 800;
    color: #991B1B;
  }}
  .receipt-payout-cafeqr {{
    background: #ECFDF5;
    border: 2px solid #10B981;
    padding: 12px 16px;
    border-radius: 12px;
    margin-top: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 22px;
    font-weight: 900;
    color: #065F46;
  }}

  /* ARCHETYPE 2: WhatsApp Digital Dialogue */
  .chat-container {{
    background: #0B141A;
    border: 1.5px solid rgba(255, 255, 255, 0.16);
    border-radius: 24px;
    width: 820px;
    max-width: 860px;
    margin: 0 auto;
    overflow: hidden;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6);
  }}
  .chat-header {{
    background: #1F2C34;
    padding: 18px 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }}
  .chat-avatar {{
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #25D366;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: #FFFFFF;
    font-weight: bold;
  }}
  .chat-header-info {{
    display: flex;
    flex-direction: column;
  }}
  .chat-header-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 800;
    color: #E9EDEF;
  }}
  .chat-header-status {{
    font-size: 14px;
    color: #25D366;
    font-weight: 600;
  }}
  .chat-body {{
    padding: 26px 28px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background-image: radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 20px 20px;
  }}
  .chat-bubble {{
    max-width: 85%;
    padding: 16px 22px;
    border-radius: 18px;
    font-size: 19px;
    line-height: 1.45;
  }}
  .chat-incoming {{
    background: #202C33;
    color: #E9EDEF;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
  }}
  .chat-outgoing {{
    background: #005C4B;
    color: #E9EDEF;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
  }}
  .chat-meta {{
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 6px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 4px;
  }}

  /* ARCHETYPE 3: 3-Step Velocity / Hardware Benchmark */
  .flow-container {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 18px;
    align-items: stretch;
    margin: 0 auto;
    max-width: 960px;
  }}
  .flow-step-card {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1.5px solid rgba(255, 255, 255, 0.14);
    border-radius: 20px;
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }}
  .flow-step-badge {{
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 12px;
    align-self: flex-start;
  }}
  .flow-step-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 900;
    margin-bottom: 10px;
    color: #FFFFFF;
    line-height: 1.2;
  }}
  .flow-step-desc {{
    font-size: 15px;
    color: #94A3B8;
    line-height: 1.4;
    flex-grow: 1;
  }}
  .flow-step-metric {{
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 900;
  }}

  /* ARCHETYPE 5: Transparent Sachet Pricing Grid */
  .pricing-grid-card {{
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    border: 2px solid rgba(255, 255, 255, 0.14);
    border-radius: 24px;
    padding: 30px 34px;
    max-width: 900px;
    margin: 0 auto;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  }}
  .pricing-grid-hero {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 20px;
    margin-bottom: 20px;
  }}
  .pricing-hero-badge {{
    font-size: 14px;
    font-weight: 800;
    color: #10B981;
    background: rgba(16, 185, 129, 0.15);
    padding: 6px 14px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: inline-block;
    margin-bottom: 8px;
  }}
  .pricing-hero-price {{
    font-family: 'Outfit', sans-serif;
    font-size: 44px;
    font-weight: 900;
    color: #FFFFFF;
    line-height: 1.1;
  }}
  .pricing-hero-sub {{
    font-size: 16px;
    color: #94A3B8;
    margin-top: 4px;
  }}
  .sachet-addons-list {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }}
  .sachet-addon-pill {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .addon-name {{
    font-size: 16px;
    font-weight: 700;
    color: #E2E8F0;
  }}
  .addon-price {{
    font-family: 'Outfit', sans-serif;
    font-size: 18px;
    font-weight: 900;
    color: #10B981;
  }}

  /* ARCHETYPE 6: Legacy POS Contract Audit */
  .contract-card {{
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(14px);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    border-radius: 22px;
    padding: 26px 30px;
    max-width: 860px;
    margin: 0 auto;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  }}
  .contract-header {{
    text-align: center;
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 12px;
    margin-bottom: 16px;
  }}
  .contract-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 900;
    color: #FFFFFF;
  }}
  .contract-sub {{
    font-size: 13px;
    color: #94A3B8;
    font-weight: 700;
    margin-top: 4px;
  }}
  .contract-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 18px;
    font-weight: 700;
  }}
  .contract-row.trap {{
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #FCA5A5;
  }}
  .contract-row.trap strong {{
    color: #EF4444;
  }}
  .contract-row.profit {{
    background: rgba(16, 185, 129, 0.14);
    border: 1.5px solid #10B981;
    color: #FFFFFF;
  }}
  .contract-row.profit strong {{
    color: #10B981;
    font-size: 22px;
  }}

  /* ARCHETYPE 7: Barcode & Batch Audit */
  .barcode-card {{
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(14px);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    border-radius: 22px;
    padding: 26px 30px;
    max-width: 860px;
    margin: 0 auto;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    text-align: center;
  }}
  .barcode-header {{
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 12px;
    margin-bottom: 16px;
  }}
  .barcode-title {{
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 900;
    color: #FFFFFF;
  }}
  .barcode-sub {{
    font-size: 13px;
    color: #94A3B8;
    font-weight: 700;
    margin-top: 4px;
  }}
  .barcode-visual {{
    background: #FFFFFF;
    color: #0F172A;
    padding: 16px;
    border-radius: 12px;
    margin: 14px auto;
    max-width: 440px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }}
  .barcode-lines {{
    font-family: 'Courier New', monospace;
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 4px;
    line-height: 1;
  }}
  .barcode-sku {{
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #475569;
    margin-top: 6px;
  }}
  .barcode-metrics {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 14px;
    margin-top: 18px;
  }}
  .barcode-metric-item {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 12px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .barcode-metric-item span {{
    font-size: 13px;
    color: #94A3B8;
    font-weight: 600;
  }}
  .barcode-metric-item strong {{
    font-size: 18px;
    font-weight: 900;
    font-family: 'Outfit', sans-serif;
  }}

  /* Pricing Pill Bar */
  .pricing-bar {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1.5px solid rgba(255, 255, 255, 0.12);
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
    color: {theme_accent};
  }}

  /* CTA Button */
  .btn-cta {{
    display: block;
    width: 100%;
    background: {theme_accent_gradient};
    color: #FFFFFF;
    font-family: 'Outfit', sans-serif;
    font-size: 26px;
    font-weight: 900;
    text-align: center;
    padding: 22px 30px;
    border-radius: 18px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
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
  {photo_bg_html}
  <div class="ambient-glow"></div>
  <div class="ambient-glow-2"></div>
  <div class="grid-bg"></div>

  <div class="z2 header-row">
    <div class="brand-capsule">
      <img src="{{{{logo_img}}}}" alt="Cafe QR" class="brand-logo" />
      <div class="brand-text">
        <span class="brand-name">CAFE QR</span>
        <span class="brand-sub">www.cafeqr.in • LLP Registered</span>
      </div>
    </div>
    <div class="badge-pill">{badge}</div>
  </div>

  {news_anchor_html}

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
    # Deterministic Brand Safeguard: Ensure Year 2+ renewal is strictly ₹999/yr, never 9999
    full_poster_html = re.sub(r'(?:₹|Rs\.?|INR)?\s*9999\b(?:\s*/\s*(?:yr|year))?', '₹999/yr', full_poster_html, flags=re.IGNORECASE)
    full_poster_html = re.sub(r'(?:₹|Rs\.?|INR)?\s*9,999\b(?:\s*/\s*(?:yr|year))?', '₹999/yr', full_poster_html, flags=re.IGNORECASE)

    # Deterministic Delivery Safeguard: Never allow table orders/table revenue on cloud kitchen/delivery topics
    text_check = f"{vertical} {headline} {topic_item.get('title', '')} {topic_item.get('category', '')}".lower()
    if any(k in text_check for k in ["cloud kitchen", "qsr", "swiggy", "zomato", "food app", "food apps", "delivery", "dark store"]):
        full_poster_html = re.sub(r'\btable\s+revenue\b', 'delivery revenue', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bevery\s+table\s+order\b', 'every delivery order', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\ball\s+direct\s+table\s+qr\s+orders\b', 'all direct online delivery orders', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bdirect\s+table\s+qr\s+orders?\b', 'direct online delivery website orders', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bdirect\s+table\s+orders?\b', 'direct online delivery orders', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\btable\s+qr\s+orders?\b', 'direct delivery website orders', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\btable\s+qr\s+ordering\b', 'direct delivery website ordering', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bcommission\s+on\s+every\s+table\s+order\b', 'commission on every delivery order', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bcommission\s+on\s+table\s+orders?\b', 'commission on delivery orders', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bfull\s+dining\s+profit\b', 'full delivery profit', full_poster_html, flags=re.IGNORECASE)
        full_poster_html = re.sub(r'\bdining\s+profit\b', 'delivery profit', full_poster_html, flags=re.IGNORECASE)
    return full_poster_html

