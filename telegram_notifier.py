import os
import json
import html
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004295934068").strip()
STUDIO_PUBLIC_URL = os.getenv("STUDIO_PUBLIC_URL", "https://cafeqr-marketing-studio.onrender.com").rstrip("/")

def _normalize_chat_id(raw_id):
    """Sanitizes chat_id and resolves legacy group IDs that were upgraded to supergroup."""
    cid = str(raw_id or "").strip()
    if cid in ("5417011867", "-5417011867"):
        return "-1004295934068"
    if not cid:
        return "-1004295934068"
    return cid

def _parse_telegram_error(err_body):
    """Parses Telegram error JSON and checks for supergroup chat migration."""
    try:
        data = json.loads(err_body)
        migrate_id = data.get("parameters", {}).get("migrate_to_chat_id")
        if migrate_id:
            return {"migrated": True, "new_chat_id": str(migrate_id), "data": data}
        return {"migrated": False, "data": data}
    except Exception:
        return {"migrated": False, "data": {}}

def _save_migrated_chat_id(new_chat_id):
    """Updates runtime environment and .env file with newly migrated supergroup chat ID."""
    global TELEGRAM_CHAT_ID
    TELEGRAM_CHAT_ID = new_chat_id
    os.environ["TELEGRAM_CHAT_ID"] = new_chat_id
    try:
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith("TELEGRAM_CHAT_ID="):
                    lines[i] = f"TELEGRAM_CHAT_ID={new_chat_id}\n"
                    break
            else:
                lines.append(f"TELEGRAM_CHAT_ID={new_chat_id}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"🔄 [TelegramNotifier] Auto-updated .env with migrated supergroup chat ID: {new_chat_id}")
    except Exception as e:
        print(f"⚠️ [TelegramNotifier] Could not persist migrated chat_id to .env: {e}")

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
    chat_id = _normalize_chat_id(os.getenv("TELEGRAM_CHAT_ID", "-1004295934068"))
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
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            pass
        parsed = _parse_telegram_error(err_body)
        if parsed.get("migrated"):
            new_id = parsed["new_chat_id"]
            print(f"🔄 [TelegramNotifier] Supergroup migration detected in test alert! Auto-migrating to: {new_id}")
            _save_migrated_chat_id(new_id)
            try:
                payload = json.dumps({
                    "chat_id": new_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [[{"text": "🌐 Open Web Studio", "url": studio_url}]]
                    }
                }).encode("utf-8")
                retry_req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(retry_req, timeout=10) as res2:
                    res2_data = json.loads(res2.read().decode())
                    if res2_data.get("ok"):
                        return {"success": True, "message_id": res2_data.get("result", {}).get("message_id"), "migrated_to": new_id}
            except Exception as retry_err:
                return {"success": False, "error": f"Auto-migration retry failed: {retry_err}"}
        return {"success": False, "error": f"{e} - Detail: {err_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_telegram_poster_alert(campaign, poster_path):
    """
    Sends a high-resolution preview of the generated marketing poster directly to
    the user's Telegram Channel or personal chat with formatted caption, trending music tip,
    and a 1-click link to review and approve in the Web Studio.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = _normalize_chat_id(os.getenv("TELEGRAM_CHAT_ID", "-1004295934068"))
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

    # Safe HTML-escaping to prevent 400 Bad Request on raw symbols (<, >, &)
    safe_badge = html.escape(str(badge))
    safe_vertical = html.escape(str(vertical))
    safe_headline = html.escape(str(headline))
    # Telegram sendPhoto caption has a STRICT 1024-character maximum limit!
    safe_caption_snippet = html.escape(str(caption)[:320].strip())
    safe_sound = html.escape(str(ig_sound))

    # Formatted Telegram Message (Kept strictly ~500 chars to never exceed 1024 limit)
    telegram_caption = (
        f"🎨 <b>NEW CAFE QR POSTER READY FOR REVIEW</b>\n\n"
        f"<b>{safe_badge}</b>\n"
        f"📌 <b>Vertical:</b> {safe_vertical}\n"
        f"📢 <b>Headline:</b> {safe_headline}\n\n"
        f"📝 <b>Caption Snippet:</b>\n"
        f"<i>\"{safe_caption_snippet}...\"</i>\n\n"
        f"🎵 <b>Trending IG Sound:</b> {safe_sound}\n\n"
        f"• Year 1: ₹2,498 | Year 2+ Renewal: ₹999/yr Forever"
    )

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    inline_keyboard = {
        "inline_keyboard": [
            [{"text": "🌐 Open Web Studio to Approve", "url": studio_url}]
        ]
    }

    def _build_multipart_payload(target_chat_id, caption_text, parse_mode="HTML"):
        boundary = "----WebKitFormBoundaryTG" + hex(int(time.time() * 1000))[2:]
        body = bytearray()
        fields = {
            "chat_id": target_chat_id,
            "caption": caption_text,
            "reply_markup": json.dumps(inline_keyboard)
        }
        if parse_mode:
            fields["parse_mode"] = parse_mode

        for k, v in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{v}\r\n".encode("utf-8"))

        if os.path.exists(poster_path):
            filename = os.path.basename(poster_path)
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode("utf-8"))
            body.extend(f"Content-Type: image/png\r\n\r\n".encode("utf-8"))
            with open(poster_path, "rb") as f:
                body.extend(f.read())
            body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        return body, headers

    # Attempt 1: Send Photo with HTML formatting
    try:
        body, headers = _build_multipart_payload(chat_id, telegram_caption, parse_mode="HTML")
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode())
            if res_data.get("ok"):
                print("📱 [TelegramNotifier] Alert with high-res poster preview dispatched to Telegram!")
                return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            pass
        print(f"⚠️ [TelegramNotifier] HTML sendPhoto failed: {e} - Detail: {err_body}")

        # Check for supergroup migration
        parsed = _parse_telegram_error(err_body)
        if parsed.get("migrated"):
            new_id = parsed["new_chat_id"]
            print(f"🔄 [TelegramNotifier] Supergroup migration detected! Auto-switching to: {new_id}")
            _save_migrated_chat_id(new_id)
            chat_id = new_id
            try:
                body, headers = _build_multipart_payload(chat_id, telegram_caption, parse_mode="HTML")
                req = urllib.request.Request(url, data=body, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as res:
                    res_data = json.loads(res.read().decode())
                    if res_data.get("ok"):
                        print(f"📱 [TelegramNotifier] Alert dispatched to newly migrated supergroup ({chat_id})!")
                        return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
            except Exception as mig_err:
                print(f"⚠️ [TelegramNotifier] Retry to migrated supergroup failed: {mig_err}")

        # Attempt 2: Fallback to plain text caption (No parse_mode)
        try:
            plain_caption = (
                f"🎨 NEW CAFE QR POSTER READY FOR REVIEW\n\n"
                f"{badge}\n"
                f"Vertical: {vertical}\n"
                f"Headline: {headline}\n\n"
                f"Caption: {caption[:300]}...\n\n"
                f"🎵 Trending IG Sound: {ig_sound}\n\n"
                f"Studio: {studio_url}\n"
                f"Year 1: ₹2,498 | Year 2+ Renewal: ₹999/yr Forever"
            )
            body, headers = _build_multipart_payload(chat_id, plain_caption, parse_mode=None)
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as res:
                res_data = json.loads(res.read().decode())
                if res_data.get("ok"):
                    print("📱 [TelegramNotifier] Plain text photo alert dispatched to Telegram!")
                    return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
        except Exception as retry_err:
            print(f"⚠️ [TelegramNotifier] Plain text photo retry also failed: {retry_err}")
    except Exception as e:
        print(f"⚠️ [TelegramNotifier] Unexpected sendPhoto error: {e}")

    # Attempt 3: If photo upload fails, send text alert with link so user NEVER misses an alert
    try:
        msg_url = f"https://api.telegram.org/bot{token}/sendMessage"
        text_payload = json.dumps({
            "chat_id": chat_id,
            "text": (
                f"🎨 <b>NEW CAFE QR POSTER READY FOR REVIEW</b>\n\n"
                f"<b>{safe_badge}</b>\n"
                f"📌 <b>Vertical:</b> {safe_vertical}\n"
                f"📢 <b>Headline:</b> {safe_headline}\n\n"
                f"🔗 <b>Open Studio to Review & Publish:</b>\n{studio_url}"
            ),
            "parse_mode": "HTML",
            "reply_markup": inline_keyboard
        }).encode("utf-8")
        msg_req = urllib.request.Request(msg_url, data=text_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(msg_req, timeout=15) as res:
            res_data = json.loads(res.read().decode())
            if res_data.get("ok"):
                print("📱 [TelegramNotifier] Text notification alert dispatched to Telegram!")
                return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            pass
        parsed = _parse_telegram_error(err_body)
        if parsed.get("migrated"):
            new_id = parsed["new_chat_id"]
            print(f"🔄 [TelegramNotifier] Supergroup migration detected on text fallback! Migrating to: {new_id}")
            _save_migrated_chat_id(new_id)
            try:
                retry_payload = json.dumps({
                    "chat_id": new_id,
                    "text": (
                        f"🎨 <b>NEW CAFE QR POSTER READY FOR REVIEW</b>\n\n"
                        f"<b>{safe_badge}</b>\n"
                        f"📌 <b>Vertical:</b> {safe_vertical}\n"
                        f"📢 <b>Headline:</b> {safe_headline}\n\n"
                        f"🔗 <b>Open Studio to Review & Publish:</b>\n{studio_url}"
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": inline_keyboard
                }).encode("utf-8")
                retry_req = urllib.request.Request(msg_url, data=retry_payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(retry_req, timeout=15) as res:
                    res_data = json.loads(res.read().decode())
                    if res_data.get("ok"):
                        print(f"📱 [TelegramNotifier] Text notification dispatched to supergroup ({new_id})!")
                        return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
            except Exception as e2:
                print(f"⚠️ [TelegramNotifier] Text fallback retry failed: {e2}")
    except Exception as fallback_err:
        print(f"⚠️ [TelegramNotifier] Text message fallback error: {fallback_err}")

    return {"success": False, "error": "All Telegram alert channels failed"}
