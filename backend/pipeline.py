"""
Pipeline Orchestrator
Chains all services: URL → Audio → Transcription → Ingredients → Cart
"""
import time
from backend.services.url_parser import parse_url
from backend.services.audio_extractor import extract_audio, cleanup_audio
from backend.services.transcriber import transcribe_audio
from backend.services.ingredient_extractor import extract_ingredients
from backend.services.cart_service import add_to_cart


async def process_url(url: str) -> dict:
    """
    Full pipeline: URL → Audio → Transcription → Ingredients → Cart
    Returns a detailed result with each step's output.
    """
    pipeline_start = time.time()
    result = {
        "url": url,
        "steps": {},
        "final_result": None,
        "error": None,
        "timing": {},
    }

    # ── Step 1: Parse URL ──────────────────────────────────────────────
    step_start = time.time()
    url_data = parse_url(url)
    result["steps"]["url_parsing"] = url_data
    result["timing"]["url_parsing"] = round(time.time() - step_start, 2)

    if not url_data["valid"]:
        result["error"] = url_data["error"]
        return result

    print(f"[Pipeline] ✅ URL parsed: {url_data['platform']} — {url_data['url']}")

    # ── Step 2: Extract Audio ──────────────────────────────────────────
    step_start = time.time()
    audio_data = extract_audio(url_data["url"], url_data["platform"])
    result["steps"]["audio_extraction"] = {
        k: v for k, v in audio_data.items() if k != "audio_path"
    }
    result["timing"]["audio_extraction"] = round(time.time() - step_start, 2)

    if audio_data["error"]:
        result["error"] = audio_data["error"]
        return result

    print(f"[Pipeline] ✅ Audio extracted: {audio_data['title']} ({audio_data['duration']}s, {audio_data['file_size_mb']}MB)")

    audio_path = audio_data["audio_path"]

    try:
        # ── Step 3: Transcribe Audio ───────────────────────────────────
        step_start = time.time()
        transcript_data = transcribe_audio(audio_path)
        result["steps"]["transcription"] = {
            "text": transcript_data["text"][:500] + "..." if transcript_data["text"] and len(transcript_data["text"]) > 500 else transcript_data["text"],
            "language": transcript_data.get("language"),
            "language_probability": transcript_data.get("language_probability"),
            "duration": transcript_data.get("duration"),
            "error": transcript_data["error"],
        }
        result["timing"]["transcription"] = round(time.time() - step_start, 2)

        if transcript_data["error"]:
            result["error"] = transcript_data["error"]
            return result

        print(f"[Pipeline] ✅ Transcribed: {len(transcript_data['text'])} chars, lang={transcript_data['language']}")

        # ── Step 4: Extract Ingredients ────────────────────────────────
        step_start = time.time()
        ingredient_data = extract_ingredients(transcript_data["text"])
        result["steps"]["ingredient_extraction"] = ingredient_data
        result["timing"]["ingredient_extraction"] = round(time.time() - step_start, 2)

        if ingredient_data["error"]:
            result["error"] = ingredient_data["error"]
            return result

        extracted = ingredient_data["data"]
        print(f"[Pipeline] ✅ Ingredients: {extracted.get('dish_name')} — {len(extracted.get('ingredients', []))} items")

        if not extracted.get("is_recipe", False):
            result["error"] = "This doesn't appear to be a recipe video."
            result["final_result"] = extracted
            return result

        # ── Step 5: Add to Cart ────────────────────────────────────────
        step_start = time.time()
        cart_data = await add_to_cart(extracted.get("ingredients", []))
        result["steps"]["cart"] = cart_data
        result["timing"]["cart"] = round(time.time() - step_start, 2)

        print(f"[Pipeline] ✅ Cart: {cart_data['summary']['total']} items processed")

        # ── Final Result ───────────────────────────────────────────────
        result["final_result"] = {
            "dish_name": extracted.get("dish_name"),
            "cuisine": extracted.get("cuisine"),
            "servings": extracted.get("servings"),
            "ingredients": extracted.get("ingredients", []),
            "notes": extracted.get("notes"),
            "cart_summary": cart_data["summary"],
            "cart_items": cart_data["results"],
        }

        result["timing"]["total"] = round(time.time() - pipeline_start, 2)
        print(f"[Pipeline] ✅ Done in {result['timing']['total']}s")

    finally:
        # Always clean up temp audio file
        cleanup_audio(audio_path)

    return result
