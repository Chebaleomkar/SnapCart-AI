"""Quick test to list available formats for a YouTube Short."""
import yt_dlp

url = "https://www.youtube.com/shorts/EQKawBWD6Ec"

with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
    info = ydl.extract_info(url, download=False)
    print(f"Title: {info.get('title')}")
    print(f"Duration: {info.get('duration')}s")
    print(f"\nAvailable formats:")
    print(f"{'ID':<10} {'EXT':<6} {'ACODEC':<12} {'VCODEC':<12} {'NOTE':<20}")
    print("-" * 60)
    for f in info.get("formats", []):
        fmt_id = f.get("format_id", "?")
        ext = f.get("ext", "?")
        acodec = f.get("acodec", "none")
        vcodec = f.get("vcodec", "none")
        note = f.get("format_note", "")
        print(f"{fmt_id:<10} {ext:<6} {acodec:<12} {vcodec:<12} {note:<20}")
