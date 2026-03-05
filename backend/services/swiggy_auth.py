"""
Swiggy MCP OAuth 2.1 Authentication Service

Implements the full OAuth 2.1 + PKCE flow for Swiggy MCP:
1. Dynamic client registration
2. Authorization URL generation
3. Token exchange
4. Token refresh
"""
import os
import hashlib
import base64
import secrets
import time
import json
import httpx
from typing import Optional

# Swiggy MCP OAuth endpoints (discovered from .well-known)
MCP_AUTH_BASE = "https://mcp.swiggy.com/auth"
AUTHORIZE_URL = f"{MCP_AUTH_BASE}/authorize"
TOKEN_URL = f"{MCP_AUTH_BASE}/token"
REGISTER_URL = f"{MCP_AUTH_BASE}/register"

# Our app's callback URL (whitelisted by Swiggy)
REDIRECT_URI = os.getenv("SWIGGY_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

# MCP scopes
SCOPES = "mcp:tools"


# ---------------------------------------------------------------------------
# PKCE Helpers
# ---------------------------------------------------------------------------

def _generate_code_verifier() -> str:
    """Generate a cryptographically random code_verifier (43-128 chars)."""
    return secrets.token_urlsafe(64)[:128]


def _generate_code_challenge(verifier: str) -> str:
    """SHA256 hash the verifier and base64url-encode it (S256 method)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


# ---------------------------------------------------------------------------
# In-Memory Token Store (per-session, v1)
# ---------------------------------------------------------------------------

class TokenStore:
    """Persistent store for OAuth session data."""

    def __init__(self, cache_file: str = ".swiggy_token.json"):
        self.cache_file = cache_file
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.code_verifier: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: float = 0
        self.state: Optional[str] = None
        self.load()

    def load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    self.client_id = data.get("client_id")
                    self.client_secret = data.get("client_secret")
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.expires_at = data.get("expires_at", 0)
            except Exception as e:
                print(f"[SwiggyAuth] ⚠️ Failed to load cache: {e}")

    def save(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump({
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.expires_at,
                }, f)
        except Exception as e:
            print(f"[SwiggyAuth] ⚠️ Failed to save cache: {e}")

    def is_authenticated(self) -> bool:
        return self.access_token is not None and time.time() < self.expires_at

    def clear(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def to_dict(self) -> dict:
        return {
            "authenticated": self.is_authenticated(),
            "expires_at": self.expires_at,
            "has_refresh_token": self.refresh_token is not None,
        }


# Global store (single-user v1)
_store = TokenStore()


def get_store() -> TokenStore:
    return _store


# ---------------------------------------------------------------------------
# OAuth Flow
# ---------------------------------------------------------------------------

async def register_client() -> dict:
    """
    Step 1: Dynamic Client Registration.
    Registers our app with Swiggy MCP to get a client_id.
    """
    store = get_store()

    # Skip if already registered
    if store.client_id:
        return {"client_id": store.client_id, "error": None}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                REGISTER_URL,
                json={
                    "client_name": "SnapCartAI",
                    "redirect_uris": [REDIRECT_URI],
                    "grant_types": ["authorization_code", "refresh_token"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "client_secret_post",
                    "scope": SCOPES,
                },
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in (200, 201):
                data = response.json()
                store.client_id = data.get("client_id")
                store.client_secret = data.get("client_secret")
                print(f"[SwiggyAuth] ✅ Registered client: {store.client_id}")
                return {"client_id": store.client_id, "error": None}
            else:
                err = response.text
                print(f"[SwiggyAuth] ❌ Registration failed: {response.status_code} — {err}")
                return {"client_id": None, "error": f"Registration failed: {err}"}

    except Exception as e:
        return {"client_id": None, "error": f"Registration error: {str(e)}"}


async def get_authorize_url() -> dict:
    """
    Step 2: Generate the OAuth authorization URL.
    The user opens this in their browser to log in to Swiggy.
    """
    store = get_store()

    # Register first if needed
    if not store.client_id:
        reg = await register_client()
        if reg.get("error"):
            return {"url": None, "error": reg["error"]}

    # Generate PKCE pair
    store.code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(store.code_verifier)

    # Generate state for CSRF protection
    store.state = secrets.token_urlsafe(32)

    # Build authorize URL
    params = {
        "response_type": "code",
        "client_id": store.client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": store.state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{AUTHORIZE_URL}?{query}"

    print(f"[SwiggyAuth] 🔗 Authorization URL generated")
    return {"url": url, "error": None}


async def exchange_code(code: str, state: str) -> dict:
    """
    Step 3: Exchange the authorization code for access + refresh tokens.
    Called after the user completes Swiggy login and is redirected back.
    """
    store = get_store()

    # Verify state
    if state != store.state:
        return {"error": "Invalid state — possible CSRF attack"}

    if not store.code_verifier:
        return {"error": "No code_verifier found — start the flow again"}

    try:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": store.client_id,
            "code_verifier": store.code_verifier,
        }

        # Include client_secret if we have one
        if store.client_secret:
            payload["client_secret"] = store.client_secret

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                data = response.json()
                store.access_token = data.get("access_token")
                store.refresh_token = data.get("refresh_token")
                expires_in = data.get("expires_in", 3600)
                store.expires_at = time.time() + expires_in

                # Clear PKCE data
                store.code_verifier = None
                store.state = None
                store.save()

                print(f"[SwiggyAuth] ✅ Authenticated! Token expires in {expires_in}s")
                return {"authenticated": True, "expires_in": expires_in, "error": None}
            else:
                err = response.text
                print(f"[SwiggyAuth] ❌ Token exchange failed: {response.status_code} — {err}")
                return {"authenticated": False, "error": f"Token exchange failed: {err}"}

    except Exception as e:
        return {"authenticated": False, "error": f"Token exchange error: {str(e)}"}


async def refresh_access_token() -> dict:
    """
    Step 4: Refresh the access token using the refresh token.
    Called automatically when the access token expires.
    """
    store = get_store()

    if not store.refresh_token:
        return {"error": "No refresh token available — re-authenticate"}

    try:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": store.refresh_token,
            "client_id": store.client_id,
        }

        if store.client_secret:
            payload["client_secret"] = store.client_secret

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                data = response.json()
                store.access_token = data.get("access_token")
                if data.get("refresh_token"):
                    store.refresh_token = data["refresh_token"]
                expires_in = data.get("expires_in", 3600)
                store.expires_at = time.time() + expires_in
                store.save()

                print(f"[SwiggyAuth] ✅ Token refreshed! Expires in {expires_in}s")
                return {"refreshed": True, "error": None}
            else:
                store.clear()
                return {"refreshed": False, "error": "Refresh failed — re-authenticate"}

    except Exception as e:
        store.clear()
        return {"refreshed": False, "error": f"Refresh error: {str(e)}"}


async def get_valid_token() -> Optional[str]:
    """Get a valid access token, refreshing if needed."""
    store = get_store()

    if not store.access_token:
        return None

    # If token is expired or about to expire (30s buffer), refresh
    if time.time() >= store.expires_at - 30:
        if store.refresh_token:
            result = await refresh_access_token()
            if result.get("error"):
                return None
        else:
            return None

    return store.access_token
