import os
import sys
import json
import mimetypes
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
    GEMINI_API_KEY
)
import trend_radar
import creative_brain
import poster_engine
import video_engine
import meta_publisher
import music_fetcher
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

            # Render Video Reel
            try:
                reel_path = video_engine.render_reel_video(campaign, voice_key=voice_pref)
                reel_filename = os.path.basename(reel_path)
                campaign["reel_url"] = f"/drafts/{reel_filename}"
                campaign["reel_file"] = reel_path
            except Exception as e:
                campaign["reel_url"] = None
                campaign["reel_error"] = str(e)

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

        # 4. API: 1-Click Publish to Meta (Facebook & Instagram)
        elif path == "/api/publish":
            image_path = body.get("image_path")
            video_path = body.get("video_path")
            caption = body.get("caption", "")
            target_fb = body.get("facebook", True)
            target_ig = body.get("instagram", False)

            results = []

            # Post to Facebook Page
            if target_fb:
                fb_res = meta_publisher.publish_to_facebook_page(
                    image_path=image_path,
                    video_path=video_path,
                    caption=caption
                )
                results.append(fb_res)

            # Post to Instagram
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
                        "platform": "Instagram",
                        "success": False,
                        "error": "Instagram requires a public HTTPS URL. Facebook direct upload succeeded."
                    })

            self._send_json({"success": True, "results": results})
            return

        # 5. API: Update Token Settings
        elif path == "/api/update-settings":
            new_token = body.get("meta_token", "").strip()
            new_gemini = body.get("gemini_key", "").strip()
            new_phone = body.get("whatsapp_phone", "").strip()

            env_lines = []
            if ENV_PATH.exists():
                with open(ENV_PATH, "r", encoding="utf-8") as f:
                    env_lines = f.readlines()

            def update_line(prefix, val):
                for i, l in enumerate(env_lines):
                    if l.startswith(prefix):
                        env_lines[i] = f"{prefix}={val}\n"
                        return
                env_lines.append(f"{prefix}={val}\n")

            if new_token:
                update_line("META_ADS_ACCESS_TOKEN", new_token)
            if new_gemini:
                update_line("GEMINI_API_KEY", new_gemini)
            if new_phone:
                update_line("WHATSAPP_DEMO_PHONE", new_phone)

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
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Studio server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
