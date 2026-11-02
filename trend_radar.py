import urllib.request
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime

# Curated RSS Streams for Indian Restaurant & Tech News
NEWS_TOPICS = [
    {
        "category": "AGGREGATOR_EXPLOITATION",
        "label": "Swiggy & Zomato Fee Hikes",
        "query": "Swiggy+OR+Zomato+platform+fee+OR+commission+OR+protest",
    },
    {
        "category": "TAX_AND_COMPLIANCE",
        "label": "Restaurant GST & Billing Scrutiny",
        "query": "restaurant+GST+OR+food+tax+dispute+OR+dining+bill",
    },
    {
        "category": "POS_AND_HARDWARE",
        "label": "POS Machine & Kitchen Tech",
        "query": "POS+machine+billing+restaurant+OR+cloud+kitchen+margins",
    },
    {
        "category": "RESTAURANT_GROWTH",
        "label": "F&B Industry & Cafe Business India",
        "query": "cafe+business+India+OR+restaurant+growth+trends",
    }
]

# Evergreen Viral Hooks (Instant fallback if internet is slow or RSS offline)
EVERGREEN_TOPICS = [
    {
        "title": "Why Restaurants Are Bleeding 28% to Aggregators While Diners Pay ₹10 Platform Fees",
        "source": "Cafe QR Industry Analysis",
        "published": "Evergreen Viral Hook",
        "category": "AGGREGATOR_EXPLOITATION",
        "link": "https://cafeqr.in",
        "summary": "Aggregators squeeze both ends: charging customers platform fees while siphoning 25-30% from the restaurant owner's top line."
    },
    {
        "title": "The ₹15,000 Upfront POS Software Lock-in: Why Legacy POS Monopolies Fear Sachet Pricing",
        "source": "F&B Tech Report",
        "published": "Evergreen Viral Hook",
        "category": "POS_AND_HARDWARE",
        "link": "https://cafeqr.in",
        "summary": "Petpooja and legacy systems lock cafes into ₹15,000 upfront charges + forced yearly renewals. Cafe QR disrupts with ₹99/mo sachet pricing."
    },
    {
        "title": "Friday Night Peak Rush: How 1 Glitch in Paper KOTs Destroys Restaurant Reputation",
        "source": "Restaurant Operations Weekly",
        "published": "Evergreen Viral Hook",
        "category": "POS_AND_HARDWARE",
        "link": "https://cafeqr.in",
        "summary": "Lost paper tokens and 20-minute billing delays create angry diners. Sub-second thermal KOTs fire instantly directly from table QR scans."
    },
    {
        "title": "Who Actually Owns Your Diner's Phone Number? The Hidden Truth Behind Food Delivery Apps",
        "source": "Independent F&B Forum",
        "published": "Evergreen Viral Hook",
        "category": "AGGREGATOR_EXPLOITATION",
        "link": "https://cafeqr.in",
        "summary": "When customers order via delivery apps, the restaurant gets zero repeat customer data. Direct QR ordering gives 100% CRM ownership."
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
                        "link": link_elem.text if link_elem is not None else "",
                        "summary": clean_html_text(desc_elem.text if desc_elem is not None else "")
                    })
        except Exception:
            continue

    if len(results) < 4:
        results.extend(EVERGREEN_TOPICS)

    return results

if __name__ == "__main__":
    news = fetch_trending_f_and_b_news(limit_per_topic=2)
    print(f"✅ Fetched {len(news)} live F&B trend radar stories.")
