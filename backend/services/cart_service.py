"""
Cart Service — Swiggy Instamart MCP Integration

Uses the authenticated MCP connection to:
1. Discover available tools
2. Search for products on Instamart
3. Add products to the user's cart

Falls back to generating search URLs when MCP is unavailable.
"""
import httpx
import json
from typing import Optional
from backend.config import SWIGGY_INSTAMART_MCP_URL
from backend.services.swiggy_auth import get_valid_token


# ---------------------------------------------------------------------------
# MCP Protocol Helpers
# ---------------------------------------------------------------------------

async def _mcp_request(method: str, params: dict, token: str) -> dict:
    """Send a JSON-RPC 2.0 request to Swiggy Instamart MCP."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                SWIGGY_INSTAMART_MCP_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {token}",
                },
            )

            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return {"success": False, "error": data["error"].get("message", "MCP error"), "data": None}
                return {"success": True, "data": data.get("result"), "error": None}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}", "data": None}

    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


# ---------------------------------------------------------------------------
# MCP Tool Discovery & Address Handling
# ---------------------------------------------------------------------------

async def discover_tools(token: str) -> dict:
    """List all available MCP tools on Swiggy Instamart."""
    result = await _mcp_request("tools/list", {}, token)
    if result["success"]:
        tools = result["data"].get("tools", []) if result["data"] else []
        return {"tools": tools, "error": None}
    else:
        return {"tools": [], "error": result["error"]}


async def get_default_address_id(token: str) -> Optional[str]:
    """Fetch user's addresses and return the first one (most recently used)."""
    result = await _mcp_request("tools/call", {"name": "get_addresses", "arguments": {}}, token)
    if result["success"]:
        content = result["data"].get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    addresses = json.loads(item["text"])
                    if isinstance(addresses, list) and len(addresses) > 0:
                        # Return the first address ID
                        return addresses[0].get("addressId")
                except:
                    pass
    return None


# ---------------------------------------------------------------------------
# Product Search via MCP
# ---------------------------------------------------------------------------

async def search_product_mcp(ingredient_name: str, address_id: str, token: str) -> dict:
    """Search for a product on Swiggy Instamart via MCP."""
    result = await _mcp_request(
        "tools/call",
        {
            "name": "search_products",
            "arguments": {
                "query": ingredient_name,
                "addressId": address_id
            },
        },
        token,
    )

    search_url = _build_search_url(ingredient_name)

    if result["success"]:
        # Extract product data from MCP response
        content = result["data"].get("content", []) if result["data"] else []
        products = []
        for item in content:
            if item.get("type") == "text":
                try:
                    text = item["text"]
                    # Swiggy MCP often returns products as a JSON string
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        products.extend(parsed)
                    elif isinstance(parsed, dict) and "products" in parsed:
                        products.extend(parsed["products"])
                except (json.JSONDecodeError, TypeError):
                    # Fallback for plain text or unexpected formats
                    pass

        return {
            "ingredient": ingredient_name,
            "status": "found" if products else "no_results",
            "products": products[:5],  # Top 5 results
            "search_url": search_url,
            "error": None,
        }
    else:
        return {
            "ingredient": ingredient_name,
            "status": "fallback",
            "products": [],
            "search_url": search_url,
            "error": result["error"],
        }


# ---------------------------------------------------------------------------
# Add to Cart via MCP
# ---------------------------------------------------------------------------

async def add_item_to_cart_mcp(spin_id: str, quantity: int, address_id: str, token: str) -> dict:
    """Add a specific product to the Swiggy Instamart cart via MCP update_cart tool."""
    result = await _mcp_request(
        "tools/call",
        {
            "name": "update_cart",
            "arguments": {
                "selectedAddressId": address_id,
                "items": [
                    {
                        "spinId": spin_id,
                        "quantity": quantity,
                    }
                ],
            },
        },
        token,
    )

    if result["success"]:
        return {"added": True, "data": result["data"], "error": None}
    else:
        return {"added": False, "data": None, "error": result["error"]}


# ---------------------------------------------------------------------------
# Main Cart Function — Process All Ingredients
# ---------------------------------------------------------------------------

async def add_to_cart(ingredients: list[dict], token: Optional[str] = None) -> dict:
    """
    Process all ingredients:
    - If authenticated: fetch address -> search via MCP -> add best match to cart
    - If not authenticated: generate search URLs as fallback
    """
    # Try to get a valid token if none provided
    if not token:
        token = await get_valid_token()

    use_mcp = token is not None
    address_id = None
    
    if use_mcp:
        address_id = await get_default_address_id(token)
        if not address_id:
            use_mcp = False
            print("[Cart] ⚠️ No address found, falling back to URLs")

    results = []
    added_count = 0
    search_count = 0
    fallback_count = 0

    for ingredient in ingredients:
        name = ingredient.get("name", "")
        if not name:
            continue

        if use_mcp and address_id:
            # Search via MCP
            search_result = await search_product_mcp(name, address_id, token)
            results.append(search_result)

            if search_result["status"] == "found" and search_result["products"]:
                # Auto-add the first (best match) product
                first_product = search_result["products"][0]
                # Swiggy MCP returns product ID as 'spinId' or 'id'
                spin_id = first_product.get("spinId") or first_product.get("id")

                if spin_id:
                    cart_result = await add_item_to_cart_mcp(str(spin_id), 1, address_id, token)
                    if cart_result["added"]:
                        search_result["cart_status"] = "added"
                        added_count += 1
                    else:
                        search_result["cart_status"] = "add_failed"
                        search_result["cart_error"] = cart_result["error"]
                        search_count += 1
                else:
                    search_result["cart_status"] = "no_spin_id"
                    search_count += 1
            else:
                search_count += 1
        else:
            # Fallback: just generate URLs
            search_url = _build_search_url(name)
            results.append({
                "ingredient": name,
                "status": "fallback",
                "products": [],
                "search_url": search_url,
                "cart_status": "not_authenticated",
                "error": None,
            })
            fallback_count += 1

    # Combined search URL
    all_names = [ing.get("name", "") for ing in ingredients if ing.get("name")]
    combined_query = ", ".join(all_names[:5])
    combined_url = _build_search_url(combined_query)

    return {
        "results": results,
        "summary": {
            "total": len(results),
            "added_to_cart": added_count,
            "searched": search_count,
            "fallback_urls": fallback_count,
            "mcp_connected": use_mcp,
            "combined_search_url": combined_url,
        },
        "error": None,
    }


def _build_search_url(query: str) -> str:
    """Build a Swiggy Instamart search URL."""
    return f"https://www.swiggy.com/instamart/search?q={query.replace(' ', '+').replace(',', '%2C')}"
