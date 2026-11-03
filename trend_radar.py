import urllib.request
import xml.etree.ElementTree as ET
import html
import re
import json
from datetime import datetime

# Curated RSS Streams for Indian Multi-Vertical Billing, Retail & Service Tech News
NEWS_TOPICS = [
    {
        "category": "AGGREGATOR_EXPLOITATION",
        "label": "Swiggy & Zomato Fee Hikes",
        "vertical": "Restaurants & Cafes",
        "query": "Swiggy+OR+Zomato+platform+fee+OR+commission+OR+protest",
    },
    {
        "category": "RETAIL_AND_BOUTIQUE",
        "label": "Boutique & Retail Billing & Barcode",
        "vertical": "Boutiques & Apparel",
        "query": "boutique+billing+software+OR+retail+barcode+scanning+India+inventory",
    },
    {
        "category": "BAKERY_AND_CONFECTIONERY",
        "label": "Bakery POS & Fresh Stock Expiry",
        "vertical": "Bakeries & Sweet Shops",
        "query": "bakery+business+India+OR+sweet+shop+billing+software+OR+FSSAI",
    },
    {
        "category": "CAR_WASH_AND_AUTO",
        "label": "Car Wash & Auto Detailing Operations",
        "vertical": "Car Washes & Service",
        "query": "car+wash+business+India+OR+auto+detailing+software+OR+service+tokens",
    },
    {
        "category": "POS_MONOPOLY_DISRUPTION",
        "label": "Legacy POS Upfront Software Lock-in",
        "vertical": "Universal Retail & Cafes",
        "query": "Petpooja+OR+POS+software+charges+upfront+OR+retail+billing+machine",
    },
    {
        "category": "TAX_AND_COMPLIANCE",
        "label": "GST & Billing Notice Scrutiny",
        "vertical": "Universal Merchants",
        "query": "shop+GST+notice+OR+restaurant+tax+dispute+OR+billing+penalty",
    },
    {
        "category": "ONDC_AND_DIRECT_COMMERCE",
        "label": "ONDC & 0% Commission Direct Selling",
        "vertical": "Restaurants & QSRs",
        "query": "ONDC+food+delivery+OR+direct+ordering+0%+commission",
    },
    {
        "category": "CREDIT_AND_UDHAAR",
        "label": "Customer Udhaar Ledger & Data Privacy",
        "vertical": "Local Shops & Cafes",
        "query": "merchant+khata+udhaar+OR+customer+data+privacy+delivery+apps",
    },
    {
        "category": "SALON_AND_SERVICES",
        "label": "Salon & Appointment Service Billing",
        "vertical": "Salons & Spas",
        "query": "salon+billing+software+India+OR+appointment+service+pos",
    },
    {
        "category": "HARDWARE_AND_SPEED",
        "label": "Sub-Second Thermal Billing & POS Speed",
        "vertical": "High-Volume Counters",
        "query": "thermal+printer+billing+speed+OR+ESC+POS+billing+counter+rush",
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

def rank_and_filter_trends(news_items, top_n=6, filter_vertical=None):
    """
    Autonomous AI Trend Ranker:
    Evaluates news stories across 10+ categories and ranks them by:
    1. Virality & Outrage potential for Indian merchants (Restaurants, Bakeries, Car Washes, Boutiques).
    2. Strategic alignment with Cafe QR's modular features (0% commission, ₹999/yr renewal, thermal billing, barcodes, Udhaar).
    """
    if filter_vertical and filter_vertical.lower() != "all":
        news_items = [item for item in news_items if filter_vertical.lower() in item.get("vertical", "").lower()]

    if not news_items:
        return EVERGREEN_TOPICS[:top_n]

    try:
        from creative_brain import call_nvidia_nim, clean_json_response
        candidates = []
        for idx, item in enumerate(news_items[:15]):
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
                
        return ranked_results if ranked_results else news_items[:top_n]
    except Exception as e:
        print(f"[TrendRadar] AI ranking fallback: {e}")
        return news_items[:top_n]

if __name__ == "__main__":
    news = fetch_trending_f_and_b_news(limit_per_topic=2)
    print(f"✅ Fetched {len(news)} multi-vertical trend stories across 10 categories.")
    ranked = rank_and_filter_trends(news, top_n=4)
    print(f"🔥 AI Top Ranked Story: {ranked[0]['title']} ({ranked[0].get('vertical')})")

