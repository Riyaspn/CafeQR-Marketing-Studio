import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
STUDIO_PUBLIC_URL = os.getenv("STUDIO_PUBLIC_URL", "https://cafeqr-marketing-studio.onrender.com").rstrip("/")

def check_telegram_bot_health():
    """Checks if Telegram bot token is configured and valid."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"configured": False, "message": "TELEGRAM_BOT_TOKEN missing in .env"}
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode())
            if data.get("ok"):
                return {"configured": True, "valid": True, "bot": data.get("result", {})}
    except Exception as e:
        return {"configured": True, "valid": False, "error": str(e)}
    return {"configured": False, "valid": False}

def send_test_alert():
    """Sends a test ping to verify bot-to-chat delivery."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    studio_url = os.getenv("STUDIO_PUBLIC_URL", "https://cafeqr-marketing-studio.onrender.com").rstrip("/")

    if not token or not chat_id:
        return {"success": False, "error": "Telegram Bot Token or Chat ID not configured in .env."}

    text = (
        "🚀 <b>Cafe QR Alert Bot Connected Successfully!</b>\n\n"
        "Your autonomous marketing bot is active and listening.\n"
        "Whenever a new multi-vertical poster is generated, you will receive:\n"
        "• High-resolution poster preview\n"
        "• Direct-response caption with hashtags\n"
        "• Recommended trending audio for Instagram\n"
        "• 1-Click link to open the Web Studio & approve\n\n"
        f"🔗 Studio: {studio_url}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[{"text": "🌐 Open Web Studio", "url": studio_url}]]
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            res_data = json.loads(res.read().decode())
            if res_data.get("ok"):
                return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
            return {"success": False, "error": res_data.get("description")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_telegram_poster_alert(campaign, poster_path):
    """
    Sends a high-resolution preview of the generated marketing poster directly to
    the user's Telegram Channel or personal chat with formatted caption, trending music tip,
    and a 1-click link to review and approve in the Web Studio.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    studio_url = os.getenv("STUDIO_PUBLIC_URL", "https://cafeqr-marketing-studio.onrender.com").rstrip("/")

    if not token or not chat_id:
        print("⚠️ [TelegramNotifier] Telegram token or chat_id not configured in .env. Skipping Telegram alert.")
        return {"success": False, "error": "Telegram credentials not configured"}

    headline = campaign.get("headline", "New Cafe QR Campaign")
    vertical = campaign.get("target_vertical", "Multi-Vertical")
    badge = campaign.get("badge", "⚡ MARKETING ALERT")
    caption = campaign.get("caption", "")
    audio_info = campaign.get("audio_profile", {})
    ig_sound = audio_info.get("trending_ig_tip", "Trending Commercial Beat")

    # Format Telegram Message
    telegram_caption = (
        f"🎨 <b>NEW CAFE QR POSTER READY FOR REVIEW</b>\n\n"
        f"<b>{badge}</b>\n"
        f"📌 <b>Vertical:</b> {vertical}\n"
        f"📢 <b>Headline:</b> {headline}\n\n"
        f"📝 <b>Caption & Hashtags:</b>\n"
        f"<blockquote>{caption[:700]}...</blockquote>\n\n"
        f"🎵 <b>Recommended Trending Audio:</b>\n"
        f"👉 <i>{ig_sound}</i> (Tap to copy in Studio)\n\n"
        f"🚀 <b>Review & 1-Click Publish:</b>\n"
        f"{studio_url}\n\n"
        f"• Year 1: ₹2,498 | Year 2+ Renewal: ₹999/yr Forever | 0% Commission"
    )

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    # Boundary for multipart upload
    import time
    boundary = "----WebKitFormBoundaryTG" + hex(int(time.time() * 1000))[2:]
    body = bytearray()

    fields = {
        "chat_id": chat_id,
        "caption": telegram_caption,
        "parse_mode": "HTML"
    }

    # Add inline buttons
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🌐 Open Web Studio to Approve", "url": studio_url}
            ]
        ]
    }
    fields["reply_markup"] = json.dumps(inline_keyboard)

    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{v}\r\n".encode("utf-8"))

    # Attach Photo
    if os.path.exists(poster_path):
        filename = os.path.basename(poster_path)
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: image/png\r\n\r\n".encode("utf-8"))
        with open(poster_path, "rb") as f:
            body.extend(f.read())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode())
            if res_data.get("ok"):
                print("📱 [TelegramNotifier] Alert with high-res poster preview dispatched to Telegram!")
                return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
            else:
                return {"success": False, "error": res_data.get("description")}
    except Exception as e:
        print(f"⚠️ [TelegramNotifier] Error sending Telegram alert: {e}")
        return {"success": False, "error": str(e)}
