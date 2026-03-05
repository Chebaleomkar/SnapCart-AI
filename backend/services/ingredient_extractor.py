"""
Ingredient Extractor Service
Uses Groq LLM to extract structured ingredients from recipe transcriptions.
"""
import json
from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_LLM_MODEL


# Lazy-loaded Groq client (avoids import-time errors)
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client

SYSTEM_PROMPT = """You are an expert chef and grocery shopping assistant. Your job is to analyze recipe video transcriptions and extract a structured list of ingredients.

RULES:
1. Extract ONLY food ingredients mentioned in the recipe. Ignore utensils, appliances, and non-food items.
2. Include quantities when mentioned. If no quantity is mentioned, estimate a reasonable amount.
3. Use common grocery store names for ingredients (e.g., "chicken breast" instead of "boneless skinless chicken").
4. Group similar items (e.g., don't list "salt" twice).
5. If the transcription is NOT a recipe or doesn't contain food-related content, return an empty ingredients list with a note.

RESPOND ONLY WITH VALID JSON in this exact format:
{
    "dish_name": "Name of the dish",
    "cuisine": "Type of cuisine (Indian, Italian, etc.)",
    "servings": "Number of servings if mentioned, else 'Not specified'",
    "ingredients": [
        {"name": "ingredient name", "quantity": "amount with unit", "category": "produce/dairy/meat/spices/pantry/frozen/other"}
    ],
    "notes": "Any important cooking notes or tips mentioned",
    "is_recipe": true
}

If NOT a recipe, respond with:
{
    "dish_name": null,
    "cuisine": null,
    "servings": null,
    "ingredients": [],
    "notes": "This doesn't appear to be a recipe video.",
    "is_recipe": false
}"""


def extract_ingredients(transcription: str) -> dict:
    """
    Extract structured ingredients from a recipe transcription using Groq LLM.
    Returns: { "data": dict, "raw_response": str, "error": str | None }
    """
    try:
        chat_completion = _get_client().chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Here is the transcription of a recipe video. Extract all ingredients:\n\n{transcription}",
                },
            ],
            model=GROQ_LLM_MODEL,
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        raw_response = chat_completion.choices[0].message.content

        # Parse the JSON response
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            return {
                "data": None,
                "raw_response": raw_response,
                "error": "LLM returned invalid JSON. Please try again.",
            }

        return {
            "data": data,
            "raw_response": raw_response,
            "error": None,
        }

    except Exception as e:
        return {
            "data": None,
            "raw_response": None,
            "error": f"Ingredient extraction failed: {str(e)}",
        }
