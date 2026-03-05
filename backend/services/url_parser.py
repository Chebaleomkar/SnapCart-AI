"""
URL Parser Service
Validates and detects the platform from a given URL.
"""
import re
from urllib.parse import urlparse


PLATFORM_PATTERNS = {
    "youtube": [
        r"(youtube\.com/watch\?v=[\w-]+)",
        r"(youtu\.be/[\w-]+)",
        r"(youtube\.com/shorts/[\w-]+)",
        r"(youtube\.com/embed/[\w-]+)",
    ],
    "instagram": [
        r"(instagram\.com/reel/[\w-]+)",
        r"(instagram\.com/p/[\w-]+)",
        r"(instagram\.com/tv/[\w-]+)",
    ],
    "tiktok": [
        r"(tiktok\.com/@[\w.-]+/video/\d+)",
        r"(tiktok\.com/t/[\w]+)",
        r"(vm\.tiktok\.com/[\w]+)",
    ],
}


def detect_platform(url: str) -> str | None:
    """Detect which platform the URL belongs to."""
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return None


def validate_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_url(url: str) -> str:
    """Remove tracking parameters and clean the URL."""
    url = url.strip()
    # Remove common tracking params
    url = re.sub(r"[&?](utm_\w+|si|feature|fbclid|igshid)=[^&]*", "", url)
    return url


def parse_url(url: str) -> dict:
    """
    Parse and validate a URL.
    Returns: { "url": str, "platform": str, "valid": bool, "error": str | None }
    """
    url = clean_url(url)

    if not validate_url(url):
        return {
            "url": url,
            "platform": None,
            "valid": False,
            "error": "Invalid URL format. Please provide a valid URL.",
        }

    platform = detect_platform(url)

    if not platform:
        return {
            "url": url,
            "platform": None,
            "valid": False,
            "error": "Unsupported platform. Currently supporting: YouTube, Instagram, TikTok.",
        }

    return {
        "url": url,
        "platform": platform,
        "valid": True,
        "error": None,
    }
