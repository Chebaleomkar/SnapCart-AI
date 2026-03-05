"""
Transcriber Service
Uses Groq's Whisper API for audio-to-text transcription.
Whisper is an open-source model by OpenAI — Groq hosts it on their LPU hardware
for blazing fast inference (~300x realtime).
"""
from groq import Groq
from backend.config import GROQ_API_KEY

# Lazy-loaded Groq client
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio file to text using Groq Whisper API.
    Returns: { "text": str, "language": str, "duration": float, "error": str | None }
    """
    try:
        client = _get_client()

        print(f"[Transcriber] Sending audio to Groq Whisper API...")

        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=("audio.webm", audio_file),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
                language=None,  # Auto-detect language
                prompt="This is a recipe or cooking video. Transcribe all speech accurately.",
            )

        text = transcription.text
        language = getattr(transcription, "language", "unknown")
        duration = getattr(transcription, "duration", 0)
        segments_raw = getattr(transcription, "segments", [])

        # Build segments list
        segment_list = []
        if segments_raw:
            for seg in segments_raw:
                segment_list.append({
                    "start": round(getattr(seg, "start", 0), 2),
                    "end": round(getattr(seg, "end", 0), 2),
                    "text": getattr(seg, "text", "").strip(),
                })

        if not text or not text.strip():
            return {
                "text": None,
                "language": language,
                "segments": [],
                "error": "No speech detected in the audio.",
            }

        print(f"[Transcriber] ✅ Transcribed: {len(text)} chars, lang={language}")

        return {
            "text": text.strip(),
            "language": language,
            "language_probability": 1.0,
            "duration": round(float(duration), 2) if duration else 0,
            "segments": segment_list,
            "error": None,
        }

    except Exception as e:
        return {
            "text": None,
            "language": None,
            "segments": [],
            "error": f"Transcription failed: {str(e)}",
        }
