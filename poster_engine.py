import os
import re
import uuid
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import BASE_DIR, TEMPLATES_DIR, DRAFTS_DIR, ASSETS_DIR

def _get_b64_asset(filename, mime=None):
    """
    Encodes an asset file into an inline Base64 data URI so Playwright renders it
    with 100% reliability with zero broken image links.
    """
    p = ASSETS_DIR / filename
    if not p.exists():
        if filename.startswith("logo"):
            for alt in ["logo.jpg", "logo_official.jpg", "logo.png", "cafeqr-logo.svg"]:
                if (ASSETS_DIR / alt).exists():
                    p = ASSETS_DIR / alt
                    break
    if p.exists():
        if mime is None:
            if p.suffix.lower() in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            elif p.suffix.lower() == ".svg":
                mime = "image/svg+xml"
            else:
                mime = "image/png"
        with open(p, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    return ""

def render_poster(creative_data, width=1080, height=1350, filename=None):
    """
    Renders an ultra-high-definition poster:
    1. Directly renders AI-generated bespoke Freeform HTML/CSS if available.
    2. Falls back gracefully to agency editorial templates if needed.
    Returns the absolute path to the generated PNG image.
    """
    template_name = creative_data.get("template", "freeform_ai")

    # Embed Base64 Assets
    logo_b64 = _get_b64_asset("logo.jpg") or _get_b64_asset("logo_official.jpg") or _get_b64_asset("logo.png")
    printer_b64 = _get_b64_asset("printer-3inch.png")
    cafe_bg_b64 = _get_b64_asset("cafe_warm_high_end_interior_1769345033566.png")
    pos_counter_b64 = _get_b64_asset("scene_pos_counter.jpg")
    table_qr_b64 = _get_b64_asset("scene_table_qr.jpg")

    # 1. Use AI-Generated Bespoke Freeform HTML/CSS Canvas
    custom_html = creative_data.get("poster_html")
    use_bespoke = bool(
        custom_html 
        and ("<!DOCTYPE html>" in custom_html or "<html" in custom_html)
        and template_name in ["freeform_ai", "bespoke_ai", ""]
    )

    if use_bespoke:
        print("🎨 [PosterEngine] Rendering AI-generated bespoke Freeform HTML canvas...")
        html_content = custom_html

        # Dynamically inject modified headline if updated in editor workbench
        new_headline = creative_data.get("headline")
        if new_headline:
            words = new_headline.split()
            if len(words) > 2:
                split_idx = max(len(words) - 3, 2)
                styled_h = f"{' '.join(words[:split_idx])} <span>{' '.join(words[split_idx:])}</span>"
            else:
                styled_h = f"<span>{new_headline}</span>"
            html_content = re.sub(r'<h1 class="headline-main">.*?</h1>', f'<h1 class="headline-main">{styled_h}</h1>', html_content, flags=re.DOTALL)

        new_subtext = creative_data.get("subtext")
        if new_subtext:
            html_content = re.sub(r'<p class="subtext-main">.*?</p>', f'<p class="subtext-main">{new_subtext}</p>', html_content, flags=re.DOTALL)

        html_content = html_content.replace("{{logo_img}}", logo_b64).replace("{logo_img}", logo_b64)
        html_content = html_content.replace("{{printer_img}}", printer_b64).replace("{printer_img}", printer_b64)
        html_content = html_content.replace("{{cafe_bg_img}}", cafe_bg_b64).replace("{cafe_bg_img}", cafe_bg_b64)
        html_content = html_content.replace("{{pos_counter_img}}", pos_counter_b64).replace("{pos_counter_img}", pos_counter_b64)
        html_content = html_content.replace("{{table_qr_img}}", table_qr_b64).replace("{table_qr_img}", table_qr_b64)
    else:
        # 2. Template fallback
        template_file = TEMPLATES_DIR / f"{template_name}.html"
        if not template_file.exists():
            template_file = TEMPLATES_DIR / "agency_editorial.html"
            
        with open(template_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        raw_headline = creative_data.get("headline", "CAFE QR BILLING ALERT")
        words = raw_headline.split()
        if len(words) > 2:
            head_first = " ".join(words[:-2])
            head_last = " ".join(words[-2:])
            styled_headline = f"{head_first} <span class='highlight'>{head_last}</span>"
        else:
            styled_headline = f"<span class='highlight'>{raw_headline}</span>"

        html_content = html_content.replace("{{logo_img}}", logo_b64)
        html_content = html_content.replace("{{printer_img}}", printer_b64)
        html_content = html_content.replace("{{cafe_bg_img}}", cafe_bg_b64)
        html_content = html_content.replace("{{headline}}", styled_headline)
        html_content = html_content.replace("{{subtext}}", creative_data.get("subtext", ""))
        html_content = html_content.replace("{{badge}}", creative_data.get("badge", "🚨 CAFE QR ALERT"))
        html_content = html_content.replace("{{source_tag}}", creative_data.get("source_tag", "Industry News"))
        html_content = html_content.replace("{{news_title}}", creative_data.get("news_title", creative_data.get("subtext", "")))
        html_content = html_content.replace("{{cta}}", creative_data.get("cta", "Reply DEMO for Free Trial"))

        comparison = creative_data.get("comparison", {})
        them_label = comparison.get("them_label", "Legacy Systems")
        us_label = comparison.get("us_label", "Cafe QR Direct Solution")
        them_pts = comparison.get("them_points", [])
        them_html = "".join([f'<div class="point-item"><div class="icon-cross">✕</div><div>{pt}</div></div>' for pt in them_pts])
        us_pts = comparison.get("us_points", [])
        us_html = "".join([f'<div class="point-item"><div class="icon-check">✓</div><div>{pt}</div></div>' for pt in us_pts])

        html_content = html_content.replace("{{them_label}}", them_label)
        html_content = html_content.replace("{{us_label}}", us_label)
        html_content = html_content.replace("{{them_points_html}}", them_html)
        html_content = html_content.replace("{{us_points_html}}", us_html)

    # Deterministic Brand Safeguard: Ensure Year 2+ renewal is strictly ₹999/yr, never 9999 or 9,999
    html_content = re.sub(r'(?:₹|Rs\.?|INR)?\s*9999\b(?:\s*/\s*(?:yr|year))?', '₹999/yr', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'(?:₹|Rs\.?|INR)?\s*9,999\b(?:\s*/\s*(?:yr|year))?', '₹999/yr', html_content, flags=re.IGNORECASE)

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
        page.set_content(html_content, wait_until="load")
        page.wait_for_timeout(250)  # Wait for Google Fonts & layout paint
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
