"""
Audio Extractor Service
Downloads audio from video URLs using yt-dlp.
"""
import os
import uuid
import subprocess
import yt_dlp
from backend.config import TEMP_AUDIO_DIR


def _check_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


HAS_FFMPEG = _check_ffmpeg()


def extract_audio(url: str, platform: str) -> dict:
    """
    Download audio-only from a video URL using yt-dlp.
    Returns: { "audio_path": str, "title": str, "duration": int, "error": str | None }
    """
    file_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(TEMP_AUDIO_DIR, f"{file_id}")

    ydl_opts = {
        # ba = best audio-only; ba* = best format containing audio (may include video)
        # This fallback chain handles YouTube Shorts which often lack separate audio streams
        "format": "ba/ba*/b",
        "outtmpl": f"{output_path}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "socket_timeout": 30,
    }

    # If ffmpeg is available, convert to mp3 for smaller file size
    if HAS_FFMPEG:
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ]

    # Platform-specific tweaks
    if platform in ("instagram", "tiktok"):
        ydl_opts["http_headers"] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)

        # Find the downloaded file (could be mp3, m4a, webm, mp4, etc.)
        audio_path = None
        possible_extensions = ["mp3", "m4a", "webm", "opus", "wav", "ogg", "mp4", "mkv"]

        for ext in possible_extensions:
            candidate = f"{output_path}.{ext}"
            if os.path.exists(candidate):
                audio_path = candidate
                break

        if not audio_path:
            # Check if any file was created with the file_id prefix
            for f in os.listdir(TEMP_AUDIO_DIR):
                if f.startswith(file_id):
                    audio_path = os.path.join(TEMP_AUDIO_DIR, f)
                    break

        if not audio_path:
            return {
                "audio_path": None,
                "title": title,
                "duration": duration,
                "error": "Audio file was not created. The video may be unavailable or geo-restricted.",
            }

        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

        return {
            "audio_path": audio_path,
            "title": title,
            "duration": duration,
            "file_size_mb": round(file_size_mb, 2),
            "error": None,
        }

    except yt_dlp.utils.DownloadError as e:
        return {
            "audio_path": None,
            "title": None,
            "duration": None,
            "error": f"Download failed: {str(e)}",
        }
    except Exception as e:
        return {
            "audio_path": None,
            "title": None,
            "duration": None,
            "error": f"Unexpected error: {str(e)}",
        }


def cleanup_audio(audio_path: str) -> None:
    """Remove temporary audio file after processing."""
    try:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception:
        pass  # Non-critical cleanup

