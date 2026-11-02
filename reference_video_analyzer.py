import os
import json
import yt_dlp
import whisper

def download_reference_video(url, output_dir="drafts/references"):
    """
    Downloads a reference video/reel and extracts rich metadata (views, likes, tags, description)
    using yt-dlp. Supports YouTube Shorts, Instagram Reels, Facebook Ads, TikTok, etc.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'writeinfojson': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get('id', 'video')
        ext = info.get('ext', 'mp4')
        video_path = os.path.join(output_dir, f"{video_id}.{ext}")
        
        metadata = {
            "id": video_id,
            "title": info.get("title", ""),
            "channel": info.get("uploader", "") or info.get("channel", ""),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "duration": info.get("duration", 0),
            "description": info.get("description", ""),
            "tags": info.get("tags", []),
            "webpage_url": info.get("webpage_url", url),
            "video_path": os.path.abspath(video_path) if os.path.exists(video_path) else None
        }
        
        return metadata

def transcribe_reference_audio(audio_or_video_path, model_size="base.en"):
    """
    Transcribes the spoken audio using OpenAI Whisper with word-level timestamps.
    """
    if not os.path.exists(audio_or_video_path):
        raise FileNotFoundError(f"Media file not found: {audio_or_video_path}")
        
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_or_video_path, word_timestamps=True)
    
    transcript = {
        "text": result.get("text", "").strip(),
        "segments": result.get("segments", []),
        "words": []
    }
    
    # Flatten word objects with timestamps
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            transcript["words"].append({
                "word": word.get("word", "").strip(),
                "start": round(word.get("start", 0.0), 2),
                "end": round(word.get("end", 0.0), 2),
                "probability": round(word.get("probability", 1.0), 2)
            })
            
    return transcript

def analyze_reference_creative(url, model_size="base.en"):
    """
    End-to-end pipeline:
    1. Downloads the viral reference video via yt-dlp
    2. Transcribes spoken dialog with OpenAI Whisper
    3. Analyzes hook velocity and structure for Cafe QR creative modeling
    """
    metadata = download_reference_video(url)
    video_path = metadata.get("video_path")
    
    transcript = None
    if video_path and os.path.exists(video_path):
        transcript = transcribe_reference_audio(video_path, model_size=model_size)
        
    hook_words = []
    if transcript and transcript.get("words"):
        # Spoken words in first 3 seconds
        hook_words = [w["word"] for w in transcript["words"] if w["start"] <= 3.0]
        
    analysis = {
        "metadata": metadata,
        "transcript": transcript.get("text") if transcript else "",
        "hook_first_3s": " ".join(hook_words) if hook_words else "N/A",
        "word_count": len(transcript["words"]) if transcript else 0,
        "duration_seconds": metadata.get("duration", 0),
        "est_speaking_wpm": round((len(transcript["words"]) / (metadata.get("duration", 1) / 60))) if transcript and metadata.get("duration") else 0
    }
    
    return analysis

if __name__ == "__main__":
    print("Reference Video Analyzer ready with yt-dlp & OpenAI Whisper.")
