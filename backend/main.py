"""
SnapCartAI — FastAPI Application
Paste a recipe video URL → Get ingredients → Add to cart
"""
import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from backend.pipeline import process_url
from backend.services.swiggy_auth import (
    get_authorize_url,
    exchange_code,
    get_store,
    get_valid_token,
)
from backend.services.cart_service import discover_tools


app = FastAPI(
    title="SnapCartAI",
    description="Paste a recipe video URL → Extract ingredients → Add to Swiggy Instamart cart",
    version="2.0.0",
)

# CORS for frontend (Next.js dev server runs on 3000)
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


# ── Health ─────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="SnapCartAI",
        version="2.0.0",
    )


# ── Auth Routes ────────────────────────────────────────────────────────

@app.get("/api/auth/status")
async def auth_status():
    """Check if the user is authenticated with Swiggy."""
    store = get_store()
    return store.to_dict()


@app.get("/api/auth/login")
async def auth_login():
    """Get the Swiggy OAuth authorization URL. Frontend opens this in a popup."""
    result = await get_authorize_url()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return {"authorize_url": result["url"]}


@app.get("/api/auth/callback")
async def auth_callback(code: str = Query(...), state: str = Query(...)):
    """
    OAuth callback — Swiggy redirects here after user logs in.
    Exchanges the authorization code for access token.
    """
    result = await exchange_code(code, state)
    if result.get("error"):
        # Return an HTML page that closes the popup and notifies the parent
        return FileResponse(
            os.path.join(os.path.dirname(__file__), "auth_error.html"),
        ) if os.path.exists(
            os.path.join(os.path.dirname(__file__), "auth_error.html")
        ) else {"error": result["error"]}

    # Return a small HTML page that sends a message to the parent window and closes
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>SnapCartAI — Connected!</title></head>
    <body style="background:#0a0a0a;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
        <div style="text-align:center">
            <h1>✅ Connected to Swiggy!</h1>
            <p>You can close this window now.</p>
            <script>
                if (window.opener) {
                    window.opener.postMessage({ type: 'SWIGGY_AUTH_SUCCESS' }, '*');
                    setTimeout(() => window.close(), 1500);
                }
            </script>
        </div>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@app.get("/api/auth/logout")
async def auth_logout():
    """Clear stored auth tokens."""
    store = get_store()
    store.clear()
    return {"logged_out": True}


@app.get("/api/mcp/tools")
async def mcp_tools():
    """Discover available MCP tools (requires auth)."""
    token = await get_valid_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated with Swiggy. Connect first.")
    result = await discover_tools(token)
    return result


@app.get("/api/debug/mcp")
async def debug_mcp():
    """Debug endpoint to check MCP status and tools."""
    token = await get_valid_token()
    store = get_store()

    status = {
        "authenticated": token is not None,
        "store": store.to_dict(),
        "tools": []
    }

    if token:
        tools_result = await discover_tools(token)
        status["tools"] = tools_result.get("tools", [])
        status["tools_error"] = tools_result.get("error")

    return status


# ── Pipeline Route ─────────────────────────────────────────────────────

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


# ── Static Files (Legacy) ─────────────────────────────────────────────

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Only mount old static frontend if it exists and no Next.js build
if os.path.exists(os.path.join(frontend_dir, "index.html")):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend."""
        return FileResponse(os.path.join(frontend_dir, "index.html"))
