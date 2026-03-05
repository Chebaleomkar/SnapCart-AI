
import asyncio
import sys
import os

# Add the project root to sys.path so we can import backend
sys.path.append(os.getcwd())

from backend.services.swiggy_auth import get_valid_token, get_store
from backend.services.cart_service import discover_tools

async def test_mcp():
    print("Checking Swiggy MCP Auth Status...")
    store = get_store()
    token = await get_valid_token()
    
    print(f"Token found in store: {token is not None}")
    if not token:
        print("No token found. User needs to connect via the browser first.")
        return

    print("Fetching available MCP tools...")
    result = await discover_tools(token)
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print("Tools discovered:")
        for tool in result.get("tools", []):
            print(f"- {tool.get('name')}: {tool.get('description')}")
            print(f"  Input Schema: {tool.get('inputSchema')}")

if __name__ == "__main__":
    asyncio.run(test_mcp())
