import os
import json
import re
from config import BRAND_NAME, BRAND_URL, WHATSAPP_DEMO_LINK, GEMINI_API_KEY
from knowledge_vault.evaluator import score_creative
import music_fetcher

def analyze_audio_situation(category, headline="", news_title=""):
    """
    Intelligent AI Sound Director: Analyzes the unique situation of each campaign
    and generates tailored audio keywords for dynamic online search.
    """
    cat = (category or "").upper()
    text = f"{category} {headline} {news_title}".lower()

    if any(k in text for k in ["15,000", "petpooja", "sachet", "renewal", "lock-in", "license", "pricing", "annual fee"]):
        return {
            "situation": "PRICE_DISRUPTION",
            "situation_label": "💸 Bold Sachet Disruption",
            "search_query": "electronic bass rhythm future bass",
            "title": "Future Bass & Punchy Disruptor",
            "genre": "Bold Disruption / Sachet Fight",
            "trending_ig_tip": "AP Dhillon — Dil Nu Instrumental (Punchy bass beat)",
            "bgm_volume": 0.18
        }
    elif any(k in text for k in ["0.8", "speed", "hardware", "thermal", "kot", "kitchen", "printer", "sub-second", "rush", "peak"]):
        return {
            "situation": "TECH_SPEED_FLEX",
            "situation_label": "⚡ High-Velocity Hardware Pulse",
            "search_query": "techno synthesizer electronic beat",
            "title": "Kinetic Electronic Tempo",
            "genre": "High Velocity / Hardware Flex",
            "trending_ig_tip": "Interworld — Metamorphosis (High-energy speed flex)",
            "bgm_volume": 0.18
        }
    elif any(k in text for k in ["swiggy", "zomato", "fee", "commission", "aggregator", "exploitation", "protest", "gst", "hike", "monopoly"]):
        return {
            "situation": "BREAKING_TENSION",
            "situation_label": "🚨 Breaking Controversy Tension",
            "search_query": "ambient synthesizer dramatic ambient",
            "title": "Dramatic Tension & News Expose",
            "genre": "Suspense / High Stakes",
            "trending_ig_tip": "Else — Paris (Popular for exposés & fee hike reactions)",
            "bgm_volume": 0.18
        }
    elif any(k in text for k in ["dine", "table", "cafe", "ambiance", "coffee", "customer", "loyalty", "breakfast", "monsoon", "dessert"]):
        return {
            "situation": "CAFE_AMBIANCE",
            "situation_label": "☕ Warm Cafe Acoustic Lounge",
            "search_query": "acoustic piano lounge chill guitar",
            "title": "Warm Acoustic & Chill Cafe Lounge",
            "genre": "Acoustic / Customer Experience",
            "trending_ig_tip": "Lofi Fruits Music — Coffee & Chill (Smooth coffeehouse vibe)",
            "bgm_volume": 0.18
        }
    else:
        # Custom topic fallback: Derive dynamic keywords directly from the headline
        clean_words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', text) if w not in ["with", "from", "that", "this", "have", "your"]]
        custom_kw = " ".join(clean_words[:3]) if clean_words else "ambient electronic synthesizer"
        return {
            "situation": "CUSTOM_SITUATION",
            "situation_label": f"🎵 Custom Situation ({' '.join(clean_words[:2]).title() or 'Dynamic'})",
            "search_query": f"{custom_kw} synthesizer",
            "title": "Custom Dynamic Online Beat",
            "genre": "Dynamic AI Live Match",
            "trending_ig_tip": "Trending Commercial Sound (Matched for topic)",
            "bgm_volume": 0.18
        }

def classify_audio_situation(category, headline=""):
    return analyze_audio_situation(category, headline)["situation"]

def build_deterministic_creative(topic_item):
    """
    Guaranteed, high-converting copy generator based on Alex Hormozi Grand Slam Offer
    and Indian restaurant merchant anti-monopoly positioning. Zero API dependency.
    """
    category = topic_item.get("category", "AGGREGATOR_EXPLOITATION")
    raw_title = topic_item.get("title", "Food Delivery Platform Fee Hikes")
    source = topic_item.get("source", "Industry Report")

    if category == "AGGREGATOR_EXPLOITATION":
        headline = "SWIGGY & ZOMATO HIKE FEES AGAIN"
        subtext = "Customers pay ₹10 extra. You lose 28% per bill. Who really wins?"
        badge = "🚨 F&B PROFIT ALERT"
        poster_template = "agency_editorial"
        
        comparison = {
            "title": "THE REAL RESTAURANT MATH",
            "them_label": "Third-Party Aggregators",
            "them_points": [
                "25% to 30% commission on every single order",
                "Aggregator owns your customer phone numbers",
                "Delayed weekly or bi-weekly payouts",
                "Customer sees 50 competitor cafes right above you"
            ],
            "us_label": "Cafe QR Direct Ordering",
            "us_points": [
                "0% commission: keep 100% of your bill value",
                "You own 100% of your diner customer database",
                "Instant UPI settlement directly to your bank",
                "Direct QR on tables & direct WhatsApp ordering link"
            ]
        }
        
        script = (
            "Diners think a 10 rupee platform fee is expensive? "
            "They have no idea that the restaurant behind the food is giving away 28 percent of the entire bill. "
            "On a 500 rupee order, 140 rupees goes straight to tech monopolies. "
            "Stop bleeding your hard-earned restaurant margins. "
            "Switch to Cafe QR: zero percent commission, direct table ordering, and instant thermal KOT. "
            "Click the link in our bio to get your free demo."
        )

        caption = (
            "🚨 THE DIRTY SECRET OF FOOD DELIVERY FEES IN INDIA:\n\n"
            f"Headlines: \"{raw_title}\"\n\n"
            "Every time platform fees go up, customers get angry. But restaurant owners suffer twice as much:\n\n"
            "❌ 25% to 30% commissions siphoned from every order\n"
            "❌ Zero access to your own customer phone numbers\n"
            "❌ Aggregators advertising your competitors on your listing\n\n"
            "💡 THE CAFE QR REVOLUTION:\n"
            "✅ 0% Commission Direct Online Delivery\n"
            "✅ Sub-second Table QR Ordering & instant UPI\n"
            "✅ You own 100% of your diner database\n"
            "✅ Sub-second thermal KOT prints directly in kitchen\n\n"
            f"👉 Comment 'DEMO' or tap here for instant setup: {WHATSAPP_DEMO_LINK}\n\n"
            "#restauranttech #cafebusiness #indianrestaurant #possoftware #swiggycommission #zomatocommission #cafeqr #kochicuisine #bangalorefoodies #restaurantmanagement #cloudkitchen"
        )

    elif category == "POS_AND_HARDWARE":
        headline = "STOP PAYING ₹15,000 UPFRONT FOR POS"
        subtext = "Why lock your cash into bloated 1990s legacy software?"
        badge = "⚡ HARDWARE & SPEED FLEX"
        poster_template = "us_vs_them"

        comparison = {
            "title": "LEGACY POS VS CAFE QR 2.0",
            "them_label": "Petpooja / POSist Monopolies",
            "them_points": [
                "₹15,000+ upfront license fee",
                "₹3,000 to ₹5,000 annual renewal trap",
                "Cluttered desktop screens built in 2005",
                "Crashes when internet drops on Friday nights"
            ],
            "us_label": "Cafe QR 2.0 Sachet Model",
            "us_points": [
                "₹99/month micro-sachet pricing",
                "No lock-in, cancel anytime freedom",
                "Lightning fast mobile & tablet billing",
                "0.8-second thermal KOT + offline sync"
            ]
        }

        script = (
            "Are you really still paying 15,000 rupees upfront for POS software? "
            "And then another 3,000 rupees every year just to keep it running? "
            "That era is officially over. "
            "Cafe QR gives you sub-second thermal printing, digital table QR ordering, "
            "and live cloud analytics for just 99 rupees a month. "
            "Save 15,000 rupees today. Send us a message for your free 7-day trial."
        )

        caption = (
            "💸 STOP FALLING FOR THE ₹15,000 POS SOFTWARE TRAP.\n\n"
            "Why do legacy POS providers demand ₹15,000 upfront before you even print your first bill?\n\n"
            "Because they know once you pay, you're locked into ₹3,000+ yearly renewals forever.\n\n"
            "We built Cafe QR 2.0 to end this:\n"
            "🔥 ₹99/Month Sachet Micro-Pricing\n"
            "🔥 0.8-Second ESC/POS Thermal Printing (USB, Bluetooth, WiFi)\n"
            "🔥 Dynamic UPI QR right on the receipt\n"
            "🔥 Works seamlessly even with slow internet\n\n"
            f"👉 Claim your free 7-day trial standee kit: {WHATSAPP_DEMO_LINK}\n\n"
            "#posmachine #restaurantbilling #petpooja #cafeqr #thermalprinter #billingsoftware #restauranttech #keralafoodies #chennaicafe #mumbaifoodie"
        )

    else:
        headline = "LOST BILLS & SLOW KOTS KILLING PEAK HOURS?"
        subtext = "How 40 tables order seamlessly without waiter delays."
        badge = "🚀 OPERATION EFFICIENCY"
        poster_template = "feature_spotlight"

        comparison = {
            "title": "PEAK RUSH SURVIVAL",
            "them_label": "Paper KOT & Waiter Dependency",
            "them_points": [
                "Waiters rushing between tables taking wrong orders",
                "Diners waving hands for 15 minutes to ask for the bill",
                "Paper tokens lost in kitchen smoke",
                "Billing bottleneck at the cash counter"
            ],
            "us_label": "Cafe QR Smart Table Flow",
            "us_points": [
                "Diner sits, scans acrylic QR, browses rich photo menu",
                "Order fires straight to kitchen printer in 0.8s",
                "Diner pays via instant dynamic UPI on receipt",
                "Table turnover increases by 35%"
            ]
        }

        script = (
            "What happens to your cafe during a Friday dinner rush? "
            "Tables waving their hands. Waiters taking wrong orders. Paper tokens getting lost. "
            "Here is the modern way: The diner scans the acrylic QR on their table. "
            "The kitchen thermal printer fires a KOT in 0.8 seconds. "
            "And they pay with dynamic UPI without waiting for a waiter. "
            "Turn tables 35 percent faster with Cafe QR. Reply DEMO for your free trial."
        )

        caption = (
            "⏱️ YOUR TABLES ARE WAITING 15 MINUTES JUST TO ORDER. HERE'S THE FIX.\n\n"
            "During peak rush, every wasted minute costs you a table turnover.\n\n"
            "With Cafe QR 2.0:\n"
            "1️⃣ Diner scans table QR on their phone (No app download needed)\n"
            "2️⃣ Rich visual menu with food photos loads in 0.5s\n"
            "3️⃣ Order prints instantly in the kitchen on high-speed thermal paper\n"
            "4️⃣ Dynamic UPI QR printed on the bill for 1-tap checkout\n\n"
            f"👉 See it live in action: {WHATSAPP_DEMO_LINK}\n\n"
            "#restaurantmanagement #cafeoperations #smartdining #cafeqr #tableturnover #indianfoodtech #qrsolutions #smartpos"
        )

    audio_profile = analyze_audio_situation(category, headline, raw_title)

    return {
        "headline": headline,
        "subtext": subtext,
        "badge": badge,
        "source_tag": source,
        "news_title": raw_title,
        "template": poster_template,
        "comparison": comparison,
        "script": script,
        "caption": caption,
        "cta": "Reply DEMO for Free 7-Day Trial",
        "audio_profile": audio_profile
    }

def generate_creative_campaign(topic_item):
    """
    Attempts to generate AI-crafted viral copy using Google Gemini free tier.
    Gracefully falls back to deterministic Hormozi-grade copy if key is unavailable.
    """
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
You are an expert restaurant marketing director and growth hacker for Cafe QR (https://cafeqr.in).
Cafe QR is an ultra-modern Indian restaurant tech solution:
- 0% Commission Direct Online Ordering (Swiggy/Zomato charge 25-30%)
- ₹99/month Sachet Pricing (Petpooja charges ₹15,000 upfront + ₹3,000 renewals)
- Sub-second (0.8s) ESC/POS Thermal Printing with Dynamic UPI QR on bills
- Table QR self-ordering that turns tables 35% faster

NEWS HEADLINE TO TREND-JACK:
"{topic_item.get('title')}"
Source: {topic_item.get('source')}

Follow the Profound & Wisprflow Conversion Copywriting Constitution:
1. Zero em dashes (never use '—'; use commas, colons, or periods).
2. Zero banned AI vocabulary (never use leverage, seamless, cutting-edge, robust, game-changer, innovate, empower, foster, delve, pivotal, crucial, vital, tapestry).
3. Zero contrast framing (never use 'It is not X, it is Y' or 'Not only X, but also Y'). State positive factual claims directly.
4. The Three Rules Gate: Every line must have concrete imagery, provable rupee figures, and claims a legacy competitor cannot make.
5. One Action Rule: End with a single clear CTA telling the merchant what they get.

Create a high-impact viral social media campaign response in strict JSON:
{{
  "headline": "Bold punchy headline in ALL CAPS, max 7 words",
  "subtext": "Sharp 1-line sub-hook highlighting the merchant pain point with exact numbers",
  "badge": "Short badge tag (e.g. 🚨 F&B PROFIT ALERT or ⚡ HARDWARE FLEX)",
  "template": "news_alert OR us_vs_them OR feature_spotlight",
  "script": "A 15-20 second conversational voiceover script for Instagram Reels. Highly engaging, direct, no fluff, ends with 'Comment DEMO for your free trial'.",
  "caption": "Full Instagram/Facebook caption with hook, bullet points, contrast, and hashtags",
  "cta": "Reply DEMO for Free 7-Day Trial"
}}
Return ONLY valid JSON.
"""
            response = model.generate_content(prompt)
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            data = json.loads(text)
            
            fallback = build_deterministic_creative(topic_item)
            data["comparison"] = fallback["comparison"]
            data["source_tag"] = topic_item.get("source", "Industry News")
            data["news_title"] = topic_item.get("title", "")
            data["evaluation"] = score_creative(data)
            data["audio_profile"] = fallback["audio_profile"]
            return data
        except Exception:
            pass

    camp = build_deterministic_creative(topic_item)
    camp["evaluation"] = score_creative(camp)
    return camp
