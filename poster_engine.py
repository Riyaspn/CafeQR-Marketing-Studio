import os
import uuid
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import BASE_DIR, TEMPLATES_DIR, DRAFTS_DIR, ASSETS_DIR

def _get_b64_asset(filename, mime="image/png"):
    """
    Encodes an asset file into an inline Base64 data URI so Playwright renders it
    with 100% reliability with zero broken image links.
    """
    p = ASSETS_DIR / filename
    if p.exists():
        with open(p, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    return ""

def render_poster(creative_data, width=1080, height=1350, filename=None):
    """
    Renders an ultra-high-definition poster from an HTML/CSS template using Playwright.
    Returns the absolute path to the generated PNG image.
    """
    template_name = creative_data.get("template", "agency_editorial")
    template_file = TEMPLATES_DIR / f"{template_name}.html"
    
    if not template_file.exists():
        template_file = TEMPLATES_DIR / "agency_editorial.html"
        
    with open(template_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Highlight keyword logic for headline
    raw_headline = creative_data.get("headline", "RESTAURANT PROFIT ALERT")
    words = raw_headline.split()
    if len(words) > 2:
        # Wrap last 2 words in highlight span
        head_first = " ".join(words[:-2])
        head_last = " ".join(words[-2:])
        styled_headline = f"{head_first} <span class='highlight'>{head_last}</span>"
    else:
        styled_headline = f"<span class='highlight'>{raw_headline}</span>"

    # Embed Base64 Assets
    logo_b64 = _get_b64_asset("logo.png", "image/png")
    if not logo_b64:
        logo_b64 = _get_b64_asset("cafeqr-logo.svg", "image/svg+xml")
    printer_b64 = _get_b64_asset("printer-3inch.png", "image/png")
    cafe_bg_b64 = _get_b64_asset("cafe_warm_high_end_interior_1769345033566.png", "image/png")

    # Replacements
    html_content = html_content.replace("{{logo_img}}", logo_b64)
    html_content = html_content.replace("{{printer_img}}", printer_b64)
    html_content = html_content.replace("{{cafe_bg_img}}", cafe_bg_b64)
    html_content = html_content.replace("{{headline}}", styled_headline)
    html_content = html_content.replace("{{subtext}}", creative_data.get("subtext", ""))
    html_content = html_content.replace("{{badge}}", creative_data.get("badge", "🚨 F&B PROFIT ALERT"))
    html_content = html_content.replace("{{source_tag}}", creative_data.get("source_tag", "Industry News"))
    html_content = html_content.replace("{{news_title}}", creative_data.get("news_title", creative_data.get("subtext", "")))
    html_content = html_content.replace("{{cta}}", creative_data.get("cta", "Reply DEMO for Free Trial"))

    # Dynamic Comparison Substitution
    comparison = creative_data.get("comparison", {})
    them_label = comparison.get("them_label", "Legacy Aggregators / POS")
    us_label = comparison.get("us_label", "Cafe QR Direct Solution")
    
    them_pts = comparison.get("them_points", [])
    them_html = "".join([f'<div class="point-item"><div class="icon-cross">✕</div><div>{pt}</div></div>' for pt in them_pts])
    
    us_pts = comparison.get("us_points", [])
    us_html = "".join([f'<div class="point-item"><div class="icon-check">✓</div><div>{pt}</div></div>' for pt in us_pts])

    html_content = html_content.replace("{{them_label}}", them_label)
    html_content = html_content.replace("{{us_label}}", us_label)
    html_content = html_content.replace("{{them_points_html}}", them_html)
    html_content = html_content.replace("{{us_points_html}}", us_html)

    if not filename:
        uid = uuid.uuid4().hex[:8]
        filename = f"poster_{template_name}_{uid}.png"

    output_path = DRAFTS_DIR / filename

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html_content, wait_until="networkidle")
        page.screenshot(path=str(output_path), full_page=False)
        browser.close()

    print(f"✅ Poster rendered: {output_path.name} ({width}x{height})")
    return str(output_path)

if __name__ == "__main__":
    test_data = {
        "template": "agency_editorial",
        "headline": "WHY PAY 28% COMMISSION ON EVERY ORDER?",
        "subtext": "Aggregators just raised platform fees again. Stop giving away your profit margin.",
        "badge": "🔥 DIRECT ORDERING 2.0"
    }
    img = render_poster(test_data, filename="agency_editorial_fixed.png")
    print(f"Generated: {img}")
