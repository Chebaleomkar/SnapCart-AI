"""
SnapCartAI — FastAPI Application
Paste a recipe video URL → Get ingredients → Add to cart
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.pipeline import process_url


app = FastAPI(
    title="SnapCartAI",
    description="Paste a recipe video URL → Extract ingredients → Add to Swiggy Instamart cart",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────────────

class ProcessURLRequest(BaseModel):
    url: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# ── API Routes ─────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="SnapCartAI",
        version="1.0.0",
    )


@app.post("/api/process-url")
async def process_video_url(request: ProcessURLRequest):
    """
    Main endpoint: Process a recipe video URL through the full pipeline.
    URL → Audio → Transcription → Ingredients → Cart
    """
    if not request.url or not request.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    result = await process_url(request.url.strip())

    if result.get("error") and not result.get("final_result"):
        raise HTTPException(
            status_code=422,
            detail={
                "message": result["error"],
                "steps": result.get("steps", {}),
                "timing": result.get("timing", {}),
            },
        )

    return result


# ── Static Files (Frontend) ───────────────────────────────────────────

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend."""
        return FileResponse(os.path.join(frontend_dir, "index.html"))
