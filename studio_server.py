import os
import sys
import json
import mimetypes
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from config import (
    BASE_DIR,
    WEB_DIR,
    DRAFTS_DIR,
    ASSETS_DIR,
    ENV_PATH,
    META_ACCESS_TOKEN,
    CAFE_QR_PAGE_ID,
    INSTAGRAM_ACCOUNT_ID,
    GEMINI_API_KEY,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    STUDIO_PUBLIC_URL,
    AUTONOMOUS_CRON_ENABLED,
    AUTONOMOUS_CRON_INTERVAL_HOURS
)
import trend_radar
import creative_brain
import poster_engine
import video_engine
import meta_publisher
import music_fetcher
import telegram_notifier
import autonomous_cron
from knowledge_vault.evaluator import score_creative

PORT = int(os.environ.get("PORT", 8899))

class StudioHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API: Fetch Trends
        if path == "/api/trends":
            trends = trend_radar.fetch_trending_f_and_b_news(limit_per_topic=3)
            self._send_json({"success": True, "trends": trends})
            return

        # 2. API: Meta Status Check
        elif path == "/api/meta-status":
            health = meta_publisher.check_token_health()
            self._send_json(health)
            return

        # 2b. API: Telegram Bot Status Check
        elif path == "/api/telegram-status":
            tg_health = telegram_notifier.check_telegram_bot_health()
            self._send_json(tg_health)
            return

        # 2c. API: Fetch Latest Auto-Generated Campaign Draft
        elif path == "/api/latest-draft":
            saved_file = DRAFTS_DIR / "saved_drafts.json"
            if saved_file.exists():
                try:
                    with open(saved_file, "r", encoding="utf-8") as f:
                        drafts = json.load(f)
                        if drafts and len(drafts) > 0:
                            self._send_json({"success": True, "draft": drafts[0]})
                            return
                except Exception as e:
                    self._send_json({"success": False, "error": str(e)})
                    return
            self._send_json({"success": False, "message": "No drafts found"})
            return

        # 2d. API: Fetch All Saved Autonomous Campaigns
        elif path == "/api/saved-campaigns":
            saved_file = DRAFTS_DIR / "saved_drafts.json"
            campaigns = []
            if saved_file.exists():
                try:
                    with open(saved_file, "r", encoding="utf-8") as f:
                        campaigns = json.load(f)
                except Exception:
                    pass
            self._send_json({"success": True, "campaigns": campaigns})
            return

        # 3. API: List Drafts
        elif path == "/api/drafts":
            draft_files = []
            for f in DRAFTS_DIR.glob("*.*"):
                if f.suffix.lower() in [".png", ".jpg", ".mp4", ".json"]:
                    draft_files.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "type": "video" if f.suffix == ".mp4" else "image" if f.suffix in [".png", ".jpg"] else "data",
                        "url": f"/drafts/{f.name}"
                    })
            self._send_json({"success": True, "drafts": sorted(draft_files, key=lambda x: x["name"], reverse=True)})
            return

        # 3b. API: Audio Info for Situation
        elif path == "/api/audio-info":
            qs = parse_qs(parsed.query)
            situation = qs.get("situation", ["BREAKING_TENSION"])[0]
            info = music_fetcher.get_audio_info(situation)
            self._send_json({"success": True, "info": info})
            return

        # 4. Serve Draft Files (Posters, MP4 Reels, & Audio Tracks)
        elif path.startswith("/drafts/"):
            subpath = path[len("/drafts/"):].lstrip("/")
            file_path = DRAFTS_DIR / subpath
            if file_path.exists() and file_path.is_file():
                self._serve_file(file_path)
            else:
                self.send_error(404, "Draft file not found")
            return

        # 5. Serve Assets
        elif path.startswith("/assets/"):
            filename = os.path.basename(path)
            file_path = ASSETS_DIR / filename
            if file_path.exists():
                self._serve_file(file_path)
            else:
                self.send_error(404, "Asset not found")
            return

        # 6. Serve Web Frontend
        elif path == "/" or path == "/index.html":
            self._serve_file(WEB_DIR / "index.html")
            return
        else:
            req_file = WEB_DIR / path.lstrip("/")
            if req_file.exists() and req_file.is_file():
                self._serve_file(req_file)
            else:
                self._serve_file(WEB_DIR / "index.html")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # 1. API: Generate Full Campaign (Copy + Poster + Reel)
        if path == "/api/generate-campaign":
            topic_item = body.get("topic", {})
            template_pref = body.get("template")
            voice_pref = body.get("voice", "prabhat")

            # Generate Copy
            campaign = creative_brain.generate_creative_campaign(topic_item)
            if template_pref:
                campaign["template"] = template_pref

            # Render Poster
            poster_path = poster_engine.render_poster(campaign)
            poster_filename = os.path.basename(poster_path)
            campaign["poster_url"] = f"/drafts/{poster_filename}"
            campaign["poster_file"] = poster_path

            # Fast-Path: Poster generation only (Instant ~2s response; Video Reel is generated on-demand via /api/render-reel)
            campaign["reel_url"] = None

            # Save draft metadata
            meta_path = DRAFTS_DIR / f"campaign_{Path(poster_filename).stem}.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(campaign, f, indent=2)

            self._send_json({"success": True, "campaign": campaign})
            return

        # 2. API: Re-Render Poster
        elif path == "/api/render-poster":
            creative_data = body.get("creative", {})
            poster_path = poster_engine.render_poster(creative_data)
            eval_data = score_creative(creative_data)
            self._send_json({
                "success": True,
                "poster_url": f"/drafts/{os.path.basename(poster_path)}",
                "poster_file": poster_path,
                "evaluation": eval_data
            })
            return

        # 2b. API: Live Viral Evaluation of Copy
        elif path == "/api/evaluate-copy":
            creative_data = body.get("creative", {})
            eval_data = score_creative(creative_data)
            self._send_json({"success": True, "evaluation": eval_data})
            return

        # 2c. API: Run Knowledge Harvester
        elif path == "/api/harvest-intel":
            from knowledge_vault.harvester import harvest_fresh_intel
            result = harvest_fresh_intel()
            self._send_json({"success": True, "result": result})
            return

        # 2d. API: Reverse-Engineer Viral URL via yt-dlp + whisper
        elif path == "/api/reverse-engineer":
            url = body.get("url", "").strip()
            vertical = body.get("vertical", "Restaurants & Cafes")
            if not url:
                self._send_json({"success": False, "error": "URL required"})
                return
            try:
                import viral_reverse_engineer
                campaign = viral_reverse_engineer.reverse_engineer_and_remaster(url, target_vertical=vertical)
                self._send_json({"success": True, "campaign": campaign})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)})
            return

        # 3. API: Re-Render Reel Video
        elif path == "/api/render-reel":
            creative_data = body.get("creative", {})
            voice_pref = body.get("voice", "prabhat")
            try:
                reel_path = video_engine.render_reel_video(creative_data, voice_key=voice_pref)
                self._send_json({
                    "success": True,
                    "reel_url": f"/drafts/{os.path.basename(reel_path)}",
                    "reel_file": reel_path
                })
            except Exception as e:
                self._send_json({"success": False, "error": str(e)})
            return

        # 3c. API: Live Search & Download Custom Online Music
        elif path == "/api/search-music":
            query = body.get("query", "").strip()
            if not query:
                self._send_json({"success": False, "error": "Query required"})
                return
            downloaded_path = music_fetcher.search_and_download_online_music(query)
            if downloaded_path:
                rel_url = f"/drafts/audio_cache/{os.path.basename(downloaded_path)}"
                self._send_json({
                    "success": True,
                    "file_path": downloaded_path,
                    "audio_url": rel_url,
                    "filename": os.path.basename(downloaded_path)
                })
            else:
                self._send_json({"success": False, "error": "No matching royalty-free audio found for this query."})
            return

        # 4. API: 1-Click Publish to Meta (Facebook, Instagram Feed & Stories)
        elif path == "/api/publish":
            image_path = body.get("image_path")
            video_path = body.get("video_path")
            caption = body.get("caption", "")
            target_fb = body.get("facebook", True)
            target_ig = body.get("instagram", False)
            target_story = body.get("story", False)

            results = []

            # Post to Facebook Page
            if target_fb:
                fb_res = meta_publisher.publish_to_facebook_page(
                    image_path=image_path,
                    video_path=video_path,
                    caption=caption
                )
                results.append(fb_res)

            # Post to Instagram Feed / Reel
            if target_ig:
                ig_public_url = body.get("public_media_url", "")
                if ig_public_url:
                    ig_res = meta_publisher.publish_to_instagram(
                        media_public_url=ig_public_url,
                        caption=caption,
                        is_video=bool(video_path)
                    )
                    results.append(ig_res)
                else:
                    results.append({
                        "platform": "Instagram Feed",
                        "success": False,
                        "error": "Instagram requires a public HTTPS URL. Facebook direct upload succeeded."
                    })

            # Post to Instagram Story
            if target_story:
                story_public_url = body.get("public_media_url", "")
                if story_public_url:
                    story_res = meta_publisher.publish_to_instagram_story(
                        media_public_url=story_public_url,
                        is_video=bool(video_path)
                    )
                    results.append(story_res)
                else:
                    results.append({
                        "platform": "Instagram Story",
                        "success": False,
                        "error": "Instagram Story requires a public HTTPS URL."
                    })

            # Auto-purge published image/video from disk & database upon successful posting
            any_success = any(r.get("success") for r in results)
            if any_success:
                try:
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)
                        print(f"🗑️ [AutoPurge] Deleted published poster from disk: {image_path}")
                    if video_path and os.path.exists(video_path):
                        os.remove(video_path)
                        print(f"🗑️ [AutoPurge] Deleted published video from disk: {video_path}")

                    # Prune from saved_drafts.json
                    saved_file = DRAFTS_DIR / "saved_drafts.json"
                    if saved_file.exists():
                        try:
                            with open(saved_file, "r", encoding="utf-8") as f:
                                saved = json.load(f)
                            saved = [d for d in saved if d.get("poster_path") != image_path]
                            with open(saved_file, "w", encoding="utf-8") as f:
                                json.dump(saved, f, indent=2)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"⚠️ [AutoPurge] Error cleaning up published files: {e}")

            self._send_json({"success": True, "results": results, "cleaned_up": any_success})
            return

        # 4b. API: Test Telegram Alert Bot
        elif path == "/api/test-telegram":
            res = telegram_notifier.send_test_alert()
            self._send_json(res)
            return

        # 4c. API: Trigger Autonomous Cron Cycle On-Demand (Asynchronous for Fast 200 OK)
        elif path == "/api/trigger-cron":
            # Fire cycle in background daemon thread so external cron pings never time out
            def run_worker():
                try:
                    autonomous_cron.run_autonomous_poster_cycle()
                except Exception as e:
                    print(f"⚠️ [TriggerCron] Background cycle error: {e}")

            t = threading.Thread(target=run_worker, daemon=True)
            t.start()
            self._send_json({
                "success": True,
                "message": "Autonomous generation cycle triggered in background. Telegram alert will arrive upon completion."
            })
            return

        # 4d. API: Manual Delete / Discard Draft
        elif path == "/api/delete-draft":
            target_path = body.get("poster_path") or body.get("poster_file")
            target_url = body.get("poster_url", "")
            if target_path and os.path.exists(target_path):
                try:
                    os.remove(target_path)
                    print(f"🗑️ [ManualDelete] Removed draft from disk: {target_path}")
                except Exception as e:
                    print(f"⚠️ [ManualDelete] Error removing file: {e}")

            saved_file = DRAFTS_DIR / "saved_drafts.json"
            if saved_file.exists():
                try:
                    with open(saved_file, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                    saved = [d for d in saved if d.get("poster_path") != target_path and (not target_url or d.get("poster_url") != target_url)]
                    with open(saved_file, "w", encoding="utf-8") as f:
                        json.dump(saved, f, indent=2)
                except Exception:
                    pass

            self._send_json({"success": True, "message": "Draft purged from disk and database."})
            return

        # 5. API: Update Token Settings
        elif path == "/api/update-settings":
            new_token = body.get("meta_token", "").strip()
            new_gemini = body.get("gemini_key", "").strip()
            new_phone = body.get("whatsapp_phone", "").strip()
            new_tg_token = body.get("telegram_token", "").strip()
            new_tg_chat = body.get("telegram_chat_id", "").strip()
            new_studio_url = body.get("studio_url", "").strip()

            env_lines = []
            if ENV_PATH.exists():
                with open(ENV_PATH, "r", encoding="utf-8") as f:
                    env_lines = f.readlines()

            def update_line(prefix, val):
                for i, l in enumerate(env_lines):
                    if l.startswith(prefix + "="):
                        env_lines[i] = f"{prefix}={val}\n"
                        return
                env_lines.append(f"{prefix}={val}\n")

            if new_token:
                update_line("META_ADS_ACCESS_TOKEN", new_token)
            if new_gemini:
                update_line("GEMINI_API_KEY", new_gemini)
            if new_phone:
                update_line("WHATSAPP_DEMO_PHONE", new_phone)
            if new_tg_token:
                update_line("TELEGRAM_BOT_TOKEN", new_tg_token)
            if new_tg_chat:
                update_line("TELEGRAM_CHAT_ID", new_tg_chat)
            if new_studio_url:
                update_line("STUDIO_PUBLIC_URL", new_studio_url)

            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.writelines(env_lines)

            self._send_json({"success": True, "message": "Settings updated successfully."})
            return

        self.send_error(404, "API route not found")

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                raw = self.rfile.read(length).decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _serve_file(self, file_path):
        mime, _ = mimetypes.guess_type(str(file_path))
        mime = mime or "application/octet-stream"
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, StudioHandler)
    print(f"\n=======================================================")
    print(f" 🚀 CAFE QR MARKETING STUDIO RUNNING")
    print(f" 🌐 URL: http://localhost:{PORT}")
    print(f"=======================================================\n")

    # Start Autonomous Background Cron Worker if enabled
    if AUTONOMOUS_CRON_ENABLED:
        def cron_worker():
            # Initial startup grace period before first autonomous sweep
            print(f"⏰ [AutonomousCron] Background scheduler active (frequency: every {AUTONOMOUS_CRON_INTERVAL_HOURS}h).")
            time.sleep(15)
            while True:
                try:
                    autonomous_cron.run_autonomous_poster_cycle()
                except Exception as e:
                    print(f"⚠️ [AutonomousCron] Background cycle error: {e}")
                time.sleep(AUTONOMOUS_CRON_INTERVAL_HOURS * 3600)

        cron_thread = threading.Thread(target=cron_worker, daemon=True)
        cron_thread.start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Studio server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
