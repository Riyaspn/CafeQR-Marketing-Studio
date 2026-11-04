import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time
from pathlib import Path
from config import (
    META_ACCESS_TOKEN,
    CAFE_QR_PAGE_ID,
    INSTAGRAM_ACCOUNT_ID,
    THREADS_ACCESS_TOKEN,
    THREADS_USER_ID,
    META_AD_ACCOUNT_ID,
    BRAND_URL
)

GRAPH_API_VERSION = "v22.0"
BASE_GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

def check_token_health(token=None):
    """
    Checks if the Meta Access Token is active and retrieves linked Facebook Page & Instagram account.
    """
    access_token = token or META_ACCESS_TOKEN
    if not access_token:
        return {
            "status": "MISSING_TOKEN",
            "message": "No Meta Access Token configured in .env",
            "valid": False
        }

    url = f"{BASE_GRAPH_URL}/me?fields=id,name&access_token={access_token}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode())
            
            # Fetch Page details and linked Instagram account
            page_url = f"{BASE_GRAPH_URL}/{CAFE_QR_PAGE_ID}?fields=name,username,instagram_business_account&access_token={access_token}"
            page_data = {}
            try:
                page_req = urllib.request.Request(page_url)
                with urllib.request.urlopen(page_req, timeout=8) as page_res:
                    page_data = json.loads(page_res.read().decode())
            except Exception:
                pass

            ig_id = page_data.get("instagram_business_account", {}).get("id") or INSTAGRAM_ACCOUNT_ID

            return {
                "status": "ACTIVE",
                "valid": True,
                "user_name": data.get("name", "Meta Account"),
                "page_name": page_data.get("name", "Cafe QR Facebook Page"),
                "page_id": CAFE_QR_PAGE_ID,
                "instagram_id": ig_id or "Not Linked / Pending"
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", "Token expired or invalid.")
        except Exception:
            msg = error_body
        return {
            "status": "EXPIRED",
            "valid": False,
            "message": msg,
            "instructions": (
                "Please generate a fresh Page Access Token from Meta Graph API Explorer "
                "(https://developers.facebook.com/tools/explorer/) with 'pages_manage_posts', "
                "'pages_read_engagement', 'instagram_basic', and 'instagram_content_publish' permissions."
            )
        }
    except Exception as e:
        return {
            "status": "NETWORK_ERROR",
            "valid": False,
            "message": str(e)
        }

def publish_to_facebook_page(image_path=None, video_path=None, caption="", image_url=None):
    """
    Publishes a photo or video directly to the Facebook Page using multipart upload,
    or falls back to public URL ingest if image_path is not on local disk.
    """
    if not META_ACCESS_TOKEN:
        return {"success": False, "error": "Missing Meta Access Token"}

    # Boundary for multipart form-data
    boundary = "----WebKitFormBoundaryCafeQR" + hex(int(time.time() * 1000))[2:]

    if video_path and os.path.exists(video_path):
        url = f"https://graph-video.facebook.com/{GRAPH_API_VERSION}/{CAFE_QR_PAGE_ID}/videos"
        file_path = video_path
        field_name = "source"
        mime_type = "video/mp4"
        extra_fields = {"description": caption, "access_token": META_ACCESS_TOKEN}
    elif image_path and os.path.exists(image_path):
        url = f"{BASE_GRAPH_URL}/{CAFE_QR_PAGE_ID}/photos"
        file_path = image_path
        field_name = "source"
        mime_type = "image/png"
        extra_fields = {"caption": caption, "access_token": META_ACCESS_TOKEN}
    elif image_url:
        url = f"{BASE_GRAPH_URL}/{CAFE_QR_PAGE_ID}/photos"
        params = urllib.parse.urlencode({
            "url": image_url,
            "caption": caption,
            "access_token": META_ACCESS_TOKEN
        }).encode("utf-8")
        req = urllib.request.Request(url, data=params, headers={"User-Agent": "CafeQR-MarketingEngine/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                res_data = json.loads(res.read().decode())
                post_id = res_data.get("id") or res_data.get("post_id")
                return {
                    "success": True,
                    "platform": "Facebook Page",
                    "post_id": post_id,
                    "permalink": f"https://facebook.com/{post_id}" if post_id else ""
                }
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            return {"success": False, "platform": "Facebook Page", "error": err}
        except Exception as e:
            return {"success": False, "platform": "Facebook Page", "error": str(e)}
    else:
        return {"success": False, "error": "No media file provided or file does not exist"}

    # Build multipart request body
    body = bytearray()
    for key, val in extra_fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{val}\r\n".encode("utf-8"))

    filename = os.path.basename(file_path)
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
    with open(file_path, "rb") as f:
        body.extend(f.read())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "CafeQR-MarketingEngine/2.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            res_data = json.loads(res.read().decode())
            post_id = res_data.get("id") or res_data.get("post_id")
            return {
                "success": True,
                "platform": "Facebook Page",
                "post_id": post_id,
                "permalink": f"https://facebook.com/{post_id}" if post_id else ""
            }
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        return {"success": False, "platform": "Facebook Page", "error": err}
    except Exception as e:
        return {"success": False, "platform": "Facebook Page", "error": str(e)}

def publish_to_instagram(media_public_url, caption="", is_video=False):
    """
    Publishes a photo or Reel to Instagram Business account via Meta Graph API.
    Note: Instagram API requires an externally reachable HTTPS URL to ingest media.
    """
    if not META_ACCESS_TOKEN:
        return {"success": False, "error": "Missing Meta Access Token"}
    if not INSTAGRAM_ACCOUNT_ID:
        return {"success": False, "error": "No linked Instagram Business Account ID specified"}

    # Step 1: Create Media Container
    container_url = f"{BASE_GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "caption": caption
    }
    if is_video:
        params["media_type"] = "REELS"
        params["video_url"] = media_public_url
    else:
        params["image_url"] = media_public_url

    encoded_params = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(container_url, data=encoded_params)

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode())
            creation_id = res_data.get("id")

        if not creation_id:
            return {"success": False, "error": "Failed to create Instagram container"}

        # Poll status until 'FINISHED' for BOTH photos and videos
        # Instagram needs time to download and process images from external URLs
        max_polls = 20 if is_video else 10
        poll_interval = 5 if is_video else 3
        for attempt in range(max_polls):
            time.sleep(poll_interval)
            status_url = f"{BASE_GRAPH_URL}/{creation_id}?fields=status_code&access_token={META_ACCESS_TOKEN}"
            try:
                status_res = json.loads(urllib.request.urlopen(status_url, timeout=10).read().decode())
                status_code = status_res.get("status_code")
                print(f"📸 [Instagram] Container {creation_id} status: {status_code} (poll {attempt+1}/{max_polls})")
                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    return {"success": False, "platform": "Instagram Feed", "error": "Instagram media processing failed"}
            except Exception as poll_err:
                print(f"⚠️ [Instagram] Poll error: {poll_err}")
        else:
            return {"success": False, "platform": "Instagram Feed", "error": f"Instagram media not ready after {max_polls * poll_interval}s"}

        # Step 2: Publish Media Container
        publish_url = f"{BASE_GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        pub_params = urllib.parse.urlencode({
            "creation_id": creation_id,
            "access_token": META_ACCESS_TOKEN
        }).encode("utf-8")
        pub_req = urllib.request.Request(publish_url, data=pub_params)
        with urllib.request.urlopen(pub_req, timeout=30) as pub_res:
            pub_data = json.loads(pub_res.read().decode())
            return {
                "success": True,
                "platform": "Instagram Feed",
                "post_id": pub_data.get("id")
            }
    except urllib.error.HTTPError as e:
        return {"success": False, "platform": "Instagram Feed", "error": e.read().decode()}
    except Exception as e:
        return {"success": False, "platform": "Instagram Feed", "error": str(e)}

def publish_to_instagram_story(media_public_url, is_video=False):
    """
    Publishes a photo or video directly to Instagram Stories via Meta Graph API.
    Note: Instagram Stories API requires media_type='STORIES' and a publicly accessible HTTPS URL.
    """
    if not META_ACCESS_TOKEN:
        return {"success": False, "error": "Missing Meta Access Token"}
    if not INSTAGRAM_ACCOUNT_ID:
        return {"success": False, "error": "No linked Instagram Business Account ID specified"}

    # Step 1: Create Story Container
    container_url = f"{BASE_GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "media_type": "STORIES"
    }
    if is_video:
        params["video_url"] = media_public_url
    else:
        params["image_url"] = media_public_url

    encoded_params = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(container_url, data=encoded_params)

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode())
            creation_id = res_data.get("id")

        if not creation_id:
            return {"success": False, "error": "Failed to create Instagram Story container"}

        # Poll status until 'FINISHED' for both photos and videos
        max_polls = 20 if is_video else 10
        poll_interval = 5 if is_video else 3
        for attempt in range(max_polls):
            time.sleep(poll_interval)
            status_url = f"{BASE_GRAPH_URL}/{creation_id}?fields=status_code&access_token={META_ACCESS_TOKEN}"
            try:
                status_res = json.loads(urllib.request.urlopen(status_url, timeout=10).read().decode())
                status_code = status_res.get("status_code")
                print(f"📸 [Instagram Story] Container {creation_id} status: {status_code} (poll {attempt+1}/{max_polls})")
                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    return {"success": False, "platform": "Instagram Story", "error": "Instagram Story media processing failed"}
            except Exception as poll_err:
                print(f"⚠️ [Instagram Story] Poll error: {poll_err}")
        else:
            return {"success": False, "platform": "Instagram Story", "error": f"Instagram Story media not ready after {max_polls * poll_interval}s"}

        # Step 2: Publish Story Container
        publish_url = f"{BASE_GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        pub_params = urllib.parse.urlencode({
            "creation_id": creation_id,
            "access_token": META_ACCESS_TOKEN
        }).encode("utf-8")
        pub_req = urllib.request.Request(publish_url, data=pub_params)
        with urllib.request.urlopen(pub_req, timeout=30) as pub_res:
            pub_data = json.loads(pub_res.read().decode())
            return {
                "success": True,
                "platform": "Instagram Story",
                "post_id": pub_data.get("id")
            }
    except urllib.error.HTTPError as e:
        return {"success": False, "platform": "Instagram Story", "error": e.read().decode()}
    except Exception as e:
        return {"success": False, "platform": "Instagram Story", "error": str(e)}

def publish_to_facebook_story(media_public_url, is_video=False):
    """
    Publishes a photo or video story to the Facebook Page via Meta Graph API.
    Flow for Photo:
      1. Upload photo to Page as unpublished/temporary (POST /{page-id}/photos with published=false, temporary=true)
      2. Publish photo story (POST /{page-id}/photo_stories?photo_id={photo_id})
    """
    if not META_ACCESS_TOKEN:
        return {"success": False, "error": "Missing Meta Access Token"}
    if not CAFE_QR_PAGE_ID:
        return {"success": False, "error": "No Facebook Page ID configured"}

    try:
        # Step 1: Upload temporary unpublished photo to Facebook Page
        photo_url = f"{BASE_GRAPH_URL}/{CAFE_QR_PAGE_ID}/photos"
        photo_params = urllib.parse.urlencode({
            "url": media_public_url,
            "published": "false",
            "temporary": "true",
            "access_token": META_ACCESS_TOKEN
        }).encode("utf-8")
        req = urllib.request.Request(photo_url, data=photo_params, headers={"User-Agent": "CafeQR-MarketingEngine/2.0"})
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode())
            photo_id = res_data.get("id")

        if not photo_id:
            return {"success": False, "platform": "Facebook Story", "error": "Failed to upload photo for story"}

        # Step 2: Publish photo story referencing uploaded photo ID
        story_url = f"{BASE_GRAPH_URL}/{CAFE_QR_PAGE_ID}/photo_stories"
        story_params = urllib.parse.urlencode({
            "photo_id": photo_id,
            "access_token": META_ACCESS_TOKEN
        }).encode("utf-8")
        story_req = urllib.request.Request(story_url, data=story_params, headers={"User-Agent": "CafeQR-MarketingEngine/2.0"})
        with urllib.request.urlopen(story_req, timeout=30) as story_res:
            story_data = json.loads(story_res.read().decode())
            post_id = story_data.get("post_id") or story_data.get("id")
            return {
                "success": True,
                "platform": "Facebook Story",
                "post_id": post_id
            }
    except urllib.error.HTTPError as e:
        return {"success": False, "platform": "Facebook Story", "error": e.read().decode()}
    except Exception as e:
        return {"success": False, "platform": "Facebook Story", "error": str(e)}

def publish_to_threads(media_public_url, caption="", is_video=False):
    """
    Publishes a photo or video post to Threads profile via Meta's Threads API.
    Flow:
      1. Determine Threads user ID (from config or /me)
      2. Create container: POST https://graph.threads.net/v1.0/{user_id}/threads
      3. Poll until container status is FINISHED
      4. Publish container: POST https://graph.threads.net/v1.0/{user_id}/threads_publish
    """
    token = THREADS_ACCESS_TOKEN or META_ACCESS_TOKEN
    if not token:
        return {"success": False, "error": "Missing Threads Access Token"}

    user_id = THREADS_USER_ID or "39929525056691523"
    threads_base = "https://graph.threads.net/v1.0"

    # Attempt to auto-resolve Threads user ID if not explicitly configured
    if not user_id:
        try:
            me_url = f"{threads_base}/me?fields=id,username&access_token={token}"
            me_req = urllib.request.Request(me_url, headers={"User-Agent": "CafeQR-MarketingEngine/2.0"})
            with urllib.request.urlopen(me_req, timeout=10) as me_res:
                me_data = json.loads(me_res.read().decode())
                user_id = me_data.get("id")
        except Exception:
            pass

    if not user_id:
        return {
            "success": False,
            "platform": "Threads Profile",
            "error": "No Threads User ID configured. Set THREADS_USER_ID in .env or Render."
        }

    # Step 1: Create Threads media container
    container_url = f"{threads_base}/{user_id}/threads"
    params = {
        "access_token": token,
        "text": caption
    }
    if is_video:
        params["media_type"] = "VIDEO"
        params["video_url"] = media_public_url
    else:
        params["media_type"] = "IMAGE"
        params["image_url"] = media_public_url

    encoded_params = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(container_url, data=encoded_params, headers={"User-Agent": "CafeQR-MarketingEngine/2.0"})

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode())
            creation_id = res_data.get("id")

        if not creation_id:
            return {"success": False, "platform": "Threads Profile", "error": "Failed to create Threads media container"}

        # Step 2: Poll container status until FINISHED
        max_polls = 20 if is_video else 10
        poll_interval = 5 if is_video else 3
        for attempt in range(max_polls):
            time.sleep(poll_interval)
            status_url = f"{threads_base}/{creation_id}?fields=status,error_message&access_token={token}"
            try:
                status_res = json.loads(urllib.request.urlopen(status_url, timeout=10).read().decode())
                status = status_res.get("status")
                print(f"🧵 [Threads] Container {creation_id} status: {status} (poll {attempt+1}/{max_polls})")
                if status == "FINISHED":
                    break
                elif status == "ERROR":
                    err_msg = status_res.get("error_message", "Threads processing error")
                    return {"success": False, "platform": "Threads Profile", "error": err_msg}
            except Exception as poll_err:
                print(f"⚠️ [Threads] Poll error: {poll_err}")
        else:
            return {"success": False, "platform": "Threads Profile", "error": f"Threads media not ready after {max_polls * poll_interval}s"}

        # Step 3: Publish container
        publish_url = f"{threads_base}/{user_id}/threads_publish"
        pub_params = urllib.parse.urlencode({
            "creation_id": creation_id,
            "access_token": token
        }).encode("utf-8")
        pub_req = urllib.request.Request(publish_url, data=pub_params, headers={"User-Agent": "CafeQR-MarketingEngine/2.0"})
        with urllib.request.urlopen(pub_req, timeout=30) as pub_res:
            pub_data = json.loads(pub_res.read().decode())
            post_id = pub_data.get("id")
            return {
                "success": True,
                "platform": "Threads Profile",
                "post_id": post_id,
                "permalink": f"https://www.threads.net/t/{post_id}" if post_id else ""
            }
    except urllib.error.HTTPError as e:
        return {"success": False, "platform": "Threads Profile", "error": e.read().decode()}
    except Exception as e:
        return {"success": False, "platform": "Threads Profile", "error": str(e)}

if __name__ == "__main__":
    health = check_token_health()
    print("Meta API Status:", json.dumps(health, indent=2))
