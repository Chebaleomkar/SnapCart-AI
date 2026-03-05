"""
Quick pipeline test with the original Hindi recipe short.
"""
import json
import time

url = "https://www.youtube.com/shorts/oDh58oNhJLs"

from backend.services.url_parser import parse_url
from backend.services.audio_extractor import extract_audio, cleanup_audio
from backend.services.transcriber import transcribe_audio
from backend.services.ingredient_extractor import extract_ingredients

print("=" * 60)
print("STEP 1: URL Parsing")
url_data = parse_url(url)
print(f"  Platform: {url_data['platform']}, Valid: {url_data['valid']}")

print("\n" + "=" * 60)
print("STEP 2: Audio Extraction")
t = time.time()
audio_data = extract_audio(url_data["url"], url_data["platform"])
print(f"  Time: {time.time() - t:.1f}s | Title: {audio_data.get('title')}")
print(f"  Duration: {audio_data.get('duration')}s | Size: {audio_data.get('file_size_mb')}MB")
if audio_data.get("error"):
    print(f"  ❌ {audio_data['error']}")
    exit(1)

print("\n" + "=" * 60)
print("STEP 3: Transcription (Groq Whisper API)")
t = time.time()
transcript_data = transcribe_audio(audio_data["audio_path"])
print(f"  Time: {time.time() - t:.1f}s | Language: {transcript_data.get('language')}")
print(f"  Text ({len(transcript_data.get('text') or '')} chars):")
print(f"  {(transcript_data.get('text') or 'NONE')[:400]}")
if transcript_data.get("error"):
    print(f"  ❌ {transcript_data['error']}")
    cleanup_audio(audio_data["audio_path"])
    exit(1)

print("\n" + "=" * 60)
print("STEP 4: Ingredient Extraction (Groq LLM)")
t = time.time()
ingredient_data = extract_ingredients(transcript_data["text"])
print(f"  Time: {time.time() - t:.1f}s")
if ingredient_data.get("data"):
    data = ingredient_data["data"]
    print(f"  Dish: {data.get('dish_name')}")
    print(f"  Cuisine: {data.get('cuisine')}")
    print(f"  Is Recipe: {data.get('is_recipe')}")
    print(f"  Ingredients ({len(data.get('ingredients', []))}):")
    for ing in data.get("ingredients", []):
        print(f"    🛒 {ing.get('name')} — {ing.get('quantity')} [{ing.get('category')}]")
    if data.get("notes"):
        print(f"  Notes: {data['notes']}")
else:
    print(f"  ❌ {ingredient_data.get('error')}")
    if ingredient_data.get("raw_response"):
        print(f"  Raw: {ingredient_data['raw_response'][:200]}")

cleanup_audio(audio_data["audio_path"])
print("\n" + "=" * 60)
print("✅ PIPELINE COMPLETE!")
