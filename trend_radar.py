import urllib.request
import xml.etree.ElementTree as ET
import html
import re
import json
from datetime import datetime

# Curated RSS Streams for Indian Multi-Vertical Billing, Retail & Service Tech News (26 Specialized Streams)
NEWS_TOPICS = [
    # 1-4: Restaurants, Cafes & Cloud Kitchens
    {
        "category": "AGGREGATOR_EXPLOITATION",
        "label": "Swiggy & Zomato Platform Fee Hikes",
        "vertical": "Restaurants & Cafes",
        "query": "Swiggy+OR+Zomato+platform+fee+hike+OR+commission+restaurant+protest",
    },
    {
        "category": "ONDC_AND_DIRECT_COMMERCE",
        "label": "ONDC & 0% Commission Direct Delivery",
        "vertical": "Restaurants & Cafes",
        "query": "ONDC+food+delivery+order+direct+restaurant+zero+commission",
    },
    {
        "category": "NRAI_AND_RESTAURANT_VOICE",
        "label": "NRAI & Restaurant Owner Outrage",
        "vertical": "Restaurants & Cafes",
        "query": "NRAI+restaurant+delivery+apps+dispute+deep+discounting",
    },
    {
        "category": "CLOUD_KITCHEN_MARGINS",
        "label": "Cloud Kitchen P&L & Dark Store Fees",
        "vertical": "Cloud Kitchens & QSRs",
        "query": "cloud+kitchen+profit+margins+delivery+commissions+India",
    },

    # 5-8: Bakeries & Sweet Shops
    {
        "category": "BAKERY_AND_CONFECTIONERY",
        "label": "Bakery POS & Fresh Stock Expiry",
        "vertical": "Bakeries & Sweet Shops",
        "query": "bakery+business+India+batch+expiry+FSSAI+billing+software",
    },
    {
        "category": "SWEET_SHOP_BILLING",
        "label": "Mithai & Sweet Shop Festival Rush",
        "vertical": "Bakeries & Sweet Shops",
        "query": "sweet+shop+mithai+billing+counter+rush+barcode+weighing",
    },
    {
        "category": "DAIRY_RAW_MATERIAL_PRICING",
        "label": "Dairy & Sugar Commodity Price Surge",
        "vertical": "Bakeries & Sweet Shops",
        "query": "milk+prices+sugar+prices+bakery+input+costs+India",
    },
    {
        "category": "BAKERY_PACKAGING_COSTS",
        "label": "Bakery Packaging & Cake Box Inflation",
        "vertical": "Bakeries & Sweet Shops",
        "query": "bakery+packaging+costs+food+delivery+box+charges",
    },

    # 9-12: Car Washes & Auto Care
    {
        "category": "CAR_WASH_AND_AUTO",
        "label": "Car Wash & Auto Detailing Tokens",
        "vertical": "Car Washes & Auto Care",
        "query": "car+wash+business+India+auto+detailing+service+tokens+software",
    },
    {
        "category": "AUTO_SERVICE_DISRUPTION",
        "label": "Digital Job Cards & WhatsApp Billing",
        "vertical": "Car Washes & Auto Care",
        "query": "garage+billing+software+job+card+WhatsApp+receipts+India",
    },
    {
        "category": "WATER_REGULATION_MANDATE",
        "label": "Water Pressure & Detailing Regulations",
        "vertical": "Car Washes & Auto Care",
        "query": "car+wash+water+recycling+pollution+control+board+notice",
    },
    {
        "category": "AUTO_CUSTOMER_RETENTION",
        "label": "Vehicle Service Reminders & CRM",
        "vertical": "Car Washes & Auto Care",
        "query": "auto+repair+customer+retention+service+reminders+software",
    },

    # 13-16: Boutiques & Fashion Retail
    {
        "category": "RETAIL_AND_BOUTIQUE",
        "label": "Boutique Barcode Billing & Inventory",
        "vertical": "Boutiques & Apparel",
        "query": "boutique+billing+software+barcode+scanning+India+inventory+apparel",
    },
    {
        "category": "FESTIVAL_CLOTHING_RUSH",
        "label": "Festival Fashion Rush & Khata Errors",
        "vertical": "Boutiques & Apparel",
        "query": "textile+shop+billing+garment+store+festival+Diwali+rush",
    },
    {
        "category": "GARMENT_BARCODE_TAGGING",
        "label": "Clothing Price Tags & Missing Stock",
        "vertical": "Boutiques & Apparel",
        "query": "apparel+store+stock+shrinkage+barcode+label+printing",
    },
    {
        "category": "FABRIC_PRICE_VOLATILITY",
        "label": "Textile Margin Squeeze & Retail Costs",
        "vertical": "Boutiques & Apparel",
        "query": "garment+retail+margins+textile+GST+cloth+merchant",
    },

    # 17-20: POS Monopoly Disruption & Hardware Speed
    {
        "category": "POS_MONOPOLY_DISRUPTION",
        "label": "Legacy POS Upfront Software Lock-in",
        "vertical": "Universal Retail & Cafes",
        "query": "Petpooja+OR+DotPe+charges+upfront+software+annual+renewal+fee",
    },
    {
        "category": "HARDWARE_AND_SPEED",
        "label": "Sub-Second Thermal Printing & Speed",
        "vertical": "High-Volume Counters",
        "query": "thermal+printer+billing+speed+counter+rush+ESC+POS",
    },
    {
        "category": "SOUNDBOX_AND_UPI_FEES",
        "label": "Paytm & PhonePe Soundbox Rental Traps",
        "vertical": "Universal Merchants",
        "query": "soundbox+monthly+rental+charges+Paytm+PhonePe+merchant",
    },
    {
        "category": "OFFLINE_BILLING_RESILIENCE",
        "label": "Internet Outage & Billing Counter Freezes",
        "vertical": "High-Volume Counters",
        "query": "cloud+POS+downtime+internet+failure+billing+counter+stuck",
    },

    # 21-24: GST, Customer Udhaar & Privacy
    {
        "category": "TAX_AND_COMPLIANCE",
        "label": "GST & Billing Notice Scrutiny",
        "vertical": "Universal Merchants",
        "query": "GST+notice+shop+billing+penalty+e+invoicing+mandate+India",
    },
    {
        "category": "CREDIT_AND_UDHAAR",
        "label": "Customer Udhaar Ledger & Data Privacy",
        "vertical": "Universal Merchants",
        "query": "merchant+khata+udhaar+bad+debt+customer+ledger+app",
    },
    {
        "category": "CUSTOMER_DATA_THEFT",
        "label": "Delivery App Customer Number Masking",
        "vertical": "Restaurants & Retail",
        "query": "food+delivery+masking+customer+phone+numbers+CRM+theft",
    },
    {
        "category": "LOCAL_COMMERCE_MARGINS",
        "label": "Kirana & Local Retail Digital Payments",
        "vertical": "Retail & Supermarkets",
        "query": "kirana+store+digital+billing+UPI+QR+margins+India",
    },

    # 25-26: Salons & Service Tech
    {
        "category": "SALON_AND_SERVICES",
        "label": "Salon & Spa Stylist Commission Billing",
        "vertical": "Salons & Spas",
        "query": "salon+billing+software+India+appointment+stylist+commission",
    },
    {
        "category": "APPOINTMENT_NO_SHOWS",
        "label": "Service Appointment No-Shows & Token Loss",
        "vertical": "Salons & Spas",
        "query": "salon+no+show+appointment+booking+advance+UPI+tokens",
    }
]

# Evergreen Multi-Vertical Viral Hooks
EVERGREEN_TOPICS = [
    {
        "title": "Why Cafes & Restaurants Are Bleeding 28% to Aggregators While Diners Pay ₹11 Platform Fees",
        "source": "Cafe QR Industry Analysis",
        "published": "Evergreen Viral Hook",
        "category": "AGGREGATOR_EXPLOITATION",
        "vertical": "Restaurants & Cafes",
        "link": "https://cafeqr.in",
        "summary": "Aggregators squeeze both ends: charging diners platform fees while taking 25-30% from the owner. Cafe QR enables direct table ordering with 0% commission."
    },
    {
        "title": "The ₹15,000 Upfront POS Lock-in: Why Legacy Retail & Food Systems Fear ₹999/Year Sachet Pricing",
        "source": "Retail Tech Watch",
        "published": "Evergreen Viral Hook",
        "category": "POS_MONOPOLY_DISRUPTION",
        "vertical": "Universal Retail & Cafes",
        "link": "https://cafeqr.in",
        "summary": "Petpooja and legacy systems lock stores into ₹15,000 upfront charges + forced yearly renewals. Cafe QR disrupts with Year 1 ₹2,498 and ₹999/yr forever."
    },
    {
        "title": "Boutiques & Bakeries Losing 12% to Missing Barcodes and Inventory Blindspots",
        "source": "Small Retail Digest",
        "published": "Evergreen Viral Hook",
        "category": "RETAIL_AND_BOUTIQUE",
        "vertical": "Boutiques & Bakeries",
        "link": "https://cafeqr.in",
        "summary": "Manual billing without barcode scanning causes cashier delays and untracked stock leakage. Cafe QR adds instant barcode scanning for just ₹999/year."
    },
    {
        "title": "Lost Service Tokens & Angry Car Wash Customers: Why Digital WhatsApp Job Cards Win",
        "source": "Auto Care India",
        "published": "Evergreen Viral Hook",
        "category": "CAR_WASH_AND_AUTO",
        "vertical": "Car Washes & Service",
        "link": "https://cafeqr.in",
        "summary": "Paper receipts get lost and phone calls interrupt detailing work. Cafe QR generates instant digital tokens and WhatsApp payment QR codes."
    },
    {
        "title": "Who Owns Your Regular Customers? Why Aggregators Mask Phone Numbers While Cafe QR Gives 100% CRM",
        "source": "Merchant Voice India",
        "published": "Evergreen Viral Hook",
        "category": "CREDIT_AND_UDHAAR",
        "vertical": "Universal Merchants",
        "link": "https://cafeqr.in",
        "summary": "When customers order through third parties, the store gets zero repeat contact data. Direct QR ordering gives 100% customer CRM and loyalty ownership."
    }
]

def clean_html_text(raw_text):
    if not raw_text:
        return ""
    clean = re.sub(r'<.*?>', '', raw_text)
    return html.unescape(clean).strip()

def fetch_trending_f_and_b_news(limit_per_topic=3):
    """
    Fetches real-time Google News RSS articles for F&B, Swiggy, Zomato, GST, and restaurant tech.
    100% Free, zero API key required.
    """
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for topic in NEWS_TOPICS:
        url = f"https://news.google.com/rss/search?q={topic['query']}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as response:
                content = response.read()
                root = ET.fromstring(content)
                items = root.findall("./channel/item")[:limit_per_topic]

                for item in items:
                    title_elem = item.find("title")
                    pub_elem = item.find("pubDate")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")

                    full_title = clean_html_text(title_elem.text) if title_elem is not None else ""
                    source_name = "Industry News"
                    clean_title = full_title
                    if " - " in full_title:
                        parts = full_title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        source_name = parts[1].strip()

                    results.append({
                        "title": clean_title,
                        "source": source_name,
                        "published": pub_elem.text if pub_elem is not None else "",
                        "category": topic["category"],
                        "category_label": topic["label"],
                        "vertical": topic.get("vertical", "Multi-Vertical"),
                        "link": link_elem.text if link_elem is not None else "",
                        "summary": clean_html_text(desc_elem.text if desc_elem is not None else "")
                    })
        except Exception:
            continue

    if len(results) < 5:
        results.extend(EVERGREEN_TOPICS)

    return results

def deep_extract_intel(news_item):
    """
    AI Deep Intelligence Extractor:
    Reads news title, summary, and category to extract:
    1. rupee_figures: Hard monetary amounts or percentages mentioned or implied.
    2. merchant_pain: Core villain or operational friction.
    3. awareness_stage: Eugene Schwartz awareness stage (Problem-Aware, Solution-Aware, Product-Aware).
    4. recommended_angle: Marketing angle (Greedy Fee Exposé, Silent Profit Leak, Rush Drama, Sachet Disruption).
    """
    try:
        from creative_brain import call_nvidia_nim, clean_json_response
        prompt = f"""
Act as the Chief Market Intelligence Officer for Cafe QR.
Analyze this Indian business news item:
TITLE: "{news_item.get('title')}"
VERTICAL: "{news_item.get('vertical')}"
SUMMARY: "{news_item.get('summary')}"

Extract marketing intelligence in strict JSON:
{{
  "rupee_figures": "Exact rupee amount or percentage if mentioned or standard industry figure (e.g. ₹14.90 fee, ₹5000/mo waste, 28% cut)",
  "merchant_pain": "The emotional villain or operational bottleneck in 8 words or less",
  "awareness_stage": "Problem-Aware | Solution-Aware | Product-Aware",
  "recommended_angle": "Greedy Fee Exposé | Silent Profit Leak | Rush-Hour Chaos | Sachet Pricing Disruption | Customer Data Heist"
}}
Return ONLY valid JSON.
"""
        messages = [
            {"role": "system", "content": "You are a direct-response intelligence analyst. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ]
        raw = call_nvidia_nim(messages, temperature=0.1, max_tokens=200, timeout=12)
        parsed = clean_json_response(raw)
        return parsed
    except Exception:
        return {
            "rupee_figures": "₹2,498 Year 1 vs ₹15,000 Legacy",
            "merchant_pain": "Legacy billing lock-in and high fees",
            "awareness_stage": "Problem-Aware",
            "recommended_angle": "Sachet Pricing Disruption"
        }

def rank_and_filter_trends(news_items, top_n=6, filter_vertical=None):
    """
    Autonomous AI Trend Ranker & Deep Extractor:
    Evaluates news stories across 26 categories and ranks them by:
    1. Virality & Outrage potential for Indian merchants (Restaurants, Bakeries, Car Washes, Boutiques).
    2. Strategic alignment with Cafe QR's modular features (0% commission, ₹999/yr renewal, thermal billing, barcodes, Udhaar).
    Attaches deep intelligence (rupee figures, awareness stage, marketing angle) to top ranked picks.
    """
    if filter_vertical and filter_vertical.lower() != "all":
        news_items = [item for item in news_items if filter_vertical.lower() in item.get("vertical", "").lower()]

    if not news_items:
        return EVERGREEN_TOPICS[:top_n]

    try:
        from creative_brain import call_nvidia_nim, clean_json_response
        # Multi-Vertical Balanced Sampling: Ensure all business sectors (Restaurants, Bakeries, Car Washes, Retail, POS) are evaluated
        candidates = []
        vert_counts = {}
        for idx, item in enumerate(news_items):
            v = item.get("vertical", "General")
            if vert_counts.get(v, 0) < 3 and len(candidates) < 20:
                vert_counts[v] = vert_counts.get(v, 0) + 1
                candidates.append({
                    "id": idx,
                    "title": item["title"],
                    "vertical": v,
                    "summary": item.get("summary", "")[:120]
                })

        # Fill remaining slots if needed
        if len(candidates) < 15:
            existing_ids = {c["id"] for c in candidates}
            for idx, item in enumerate(news_items):
                if idx not in existing_ids and len(candidates) < 20:
                    candidates.append({
                        "id": idx,
                        "title": item["title"],
                        "vertical": item.get("vertical", "General"),
                        "summary": item.get("summary", "")[:120]
                    })

        prompt = f"""
You are the Chief Trend Strategist for Cafe QR (Indian billing, table QR & retail software used by restaurants, bakeries, car washes, and boutiques).
Analyze these recent news candidates and rank the top {top_n} stories based on merchant outrage, urgency, and marketing conversion potential.

CANDIDATES:
{json.dumps(candidates, indent=2)}

Return ONLY valid JSON matching this schema:
{{
  "ranked_ids": [0, 2, 5],
  "reasoning": "Brief 1-line reason for top pick"
}}
"""
        messages = [
            {"role": "system", "content": "You are a direct-response trend strategist. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ]
        raw = call_nvidia_nim(messages, temperature=0.2, max_tokens=250, timeout=15)
        parsed = clean_json_response(raw)
        ranked_ids = parsed.get("ranked_ids", [])
        
        ranked_results = []
        for rid in ranked_ids:
            if 0 <= rid < len(news_items):
                ranked_results.append(news_items[rid])
        
        # Fill remaining slots up to top_n if LLM returned fewer
        for item in news_items:
            if item not in ranked_results and len(ranked_results) < top_n:
                ranked_results.append(item)
                
        final_list = ranked_results if ranked_results else news_items[:top_n]
        # Attach deep intelligence to the top picks
        for item in final_list[:top_n]:
            if "deep_intel" not in item:
                item["deep_intel"] = deep_extract_intel(item)
        return final_list[:top_n]
    except Exception as e:
        print(f"[TrendRadar] AI ranking fallback: {e}")
        fallback_list = news_items[:top_n]
        for item in fallback_list:
            if "deep_intel" not in item:
                item["deep_intel"] = deep_extract_intel(item)
        return fallback_list

def fetch_trending_topics(limit=15):
    """
    Autonomous Pipeline Interface:
    Fetches multi-vertical real-time news across all 26 streams and applies AI ranking + deep intelligence.
    """
    raw_news = fetch_trending_f_and_b_news(limit_per_topic=2)
    return rank_and_filter_trends(raw_news, top_n=limit)

if __name__ == "__main__":
    news = fetch_trending_f_and_b_news(limit_per_topic=2)
    print(f"✅ Fetched {len(news)} multi-vertical trend stories across 10 categories.")
    ranked = rank_and_filter_trends(news, top_n=4)
    print(f"🔥 AI Top Ranked Story: {ranked[0]['title']} ({ranked[0].get('vertical')})")

