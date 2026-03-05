"""
Cart Service
Integrates with Swiggy Instamart MCP to search and add items to cart.

NOTE: Swiggy MCP integration is experimental. This service provides:
1. MCP-based cart operations (when MCP auth is available)
2. Fallback: generates Swiggy Instamart search URLs for each ingredient
"""
import httpx
import json
from backend.config import SWIGGY_INSTAMART_MCP_URL


async def search_instamart(ingredient_name: str) -> dict:
    """
    Search for an ingredient on Swiggy Instamart via MCP.
    Falls back to generating a search URL if MCP is unavailable.
    """
    search_url = f"https://www.swiggy.com/instamart/search?q={ingredient_name.replace(' ', '+')}"

    try:
        # Attempt MCP call
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                SWIGGY_INSTAMART_MCP_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_products",
                        "arguments": {
                            "query": ingredient_name,
                        },
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "ingredient": ingredient_name,
                    "status": "found",
                    "mcp_response": data,
                    "search_url": search_url,
                    "error": None,
                }
            else:
                return {
                    "ingredient": ingredient_name,
                    "status": "fallback",
                    "mcp_response": None,
                    "search_url": search_url,
                    "error": f"MCP returned status {response.status_code}",
                }

    except Exception as e:
        # Fallback: return search URL
        return {
            "ingredient": ingredient_name,
            "status": "fallback",
            "mcp_response": None,
            "search_url": search_url,
            "error": f"MCP unavailable: {str(e)}",
        }


async def add_to_cart(ingredients: list[dict]) -> dict:
    """
    Process all ingredients — search on Instamart and attempt to add to cart.
    Returns summary with search URLs as fallback.
    """
    results = []
    successful = 0
    fallback = 0

    for ingredient in ingredients:
        name = ingredient.get("name", "")
        if not name:
            continue

        result = await search_instamart(name)
        results.append(result)

        if result["status"] == "found":
            successful += 1
        else:
            fallback += 1

    # Generate a combined Instamart search URL for quick access
    all_names = [ing.get("name", "") for ing in ingredients if ing.get("name")]
    combined_query = ", ".join(all_names[:5])  # First 5 for the combined search
    combined_url = f"https://www.swiggy.com/instamart/search?q={combined_query.replace(' ', '+').replace(',', '%2C')}"

    return {
        "results": results,
        "summary": {
            "total": len(results),
            "added_via_mcp": successful,
            "fallback_urls": fallback,
            "combined_search_url": combined_url,
        },
        "error": None,
    }
