"""
SnapCartAI Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory (where this file lives)
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")

# --- API Keys ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Model Configuration ---
# Use "base" for CPU (fast, ~30s for 90s audio)
# Use "large-v3-turbo" for GPU (best accuracy, needs CUDA)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
GROQ_LLM_MODEL = "llama-3.3-70b-versatile"

# --- Swiggy MCP ---
SWIGGY_INSTAMART_MCP_URL = "https://mcp.swiggy.com/im"

# --- Paths ---
TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "temp_audio")
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# --- Supported Platforms ---
SUPPORTED_PLATFORMS = ["youtube", "instagram", "tiktok"]
