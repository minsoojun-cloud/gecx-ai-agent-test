import os
import json
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from google.cloud import retail_v2
from google.api_core.client_options import ClientOptions

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware
from starlette.types import ASGIApp

# Monkeypatch to ensure compatibility with Vertex AI Agent Builder (GECX)
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.server.fastmcp.server import FastMCP
from mcp.types import Tool as MCPTool

# 1. Bypass strict Accept header validation
def loose_check_accept_headers(self, request):
    return True, True
StreamableHTTPServerTransport._check_accept_headers = loose_check_accept_headers

# 2. Return minimal tool definitions (GECX prefers standard name/description/inputSchema)
# Aggressively clean up schemas and descriptions to avoid deserialization errors.
import inspect

def clean_schema(schema):
    """Recursively remove fields that often cause issues in strict parsers."""
    if not isinstance(schema, dict):
        return schema
    
    # Remove fields that are often problematic or redundant
    schema.pop("title", None)
    schema.pop("default", None)
    
    # Recursively clean properties
    if "properties" in schema:
        for prop in schema["properties"].values():
            clean_schema(prop)
    
    # Recursively clean any internal dictionaries
    for k, v in list(schema.items()):
        if isinstance(v, dict):
            clean_schema(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    clean_schema(item)
    return schema

async def list_tools_minimal(self) -> list[MCPTool]:
    tools = self._tool_manager.list_tools()
    result = []
    for info in tools:
        # Clean the description using cleandoc (removes indents and leading/trailing newlines)
        cleaned_desc = inspect.cleandoc(info.description) if info.description else ""
        
        # Aggressively clean the input schema
        cleaned_schema = clean_schema(info.parameters.copy())
        
        result.append(
            MCPTool(
                name=info.name,
                description=cleaned_desc,
                inputSchema=cleaned_schema,
            )
        )
    return result
FastMCP.list_tools = list_tools_minimal

# Initialize FastMCP Server
mcp = FastMCP(
    "VertexCommerceMCP",
    stateless_http=True,  # Required for Vertex AI Agent Builder (stateless requests)
    json_response=True,   # Force JSON responses instead of SSE for better compatibility
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

from concurrent.futures import ThreadPoolExecutor

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "ai-commerce-search-ni-osaka")
LOCATION = os.getenv("LOCATION", "global") # Retail API is usually global
CATALOG = os.getenv("CATALOG", "default_catalog")
SERVING_CONFIG = os.getenv("SERVING_CONFIG", "default_search")

# Helper to format resource names
def get_catalog_name():
    return f"projects/{PROJECT_ID}/locations/{LOCATION}/catalogs/{CATALOG}"

def _fetch_product_details(product_client, result, catalog_name):
    product_id = result.id
    p = result.product
    
    # If the product in search results lacks metadata, fetch the full product resource
    if not getattr(p, 'title', None) or not getattr(p, 'images', None) or not getattr(p, 'uri', None):
        try:
            prod_name = p.name if getattr(p, 'name', None) else f"{catalog_name}/branches/default_branch/products/{product_id}"
            p = product_client.get_product(name=prod_name)
        except Exception:
            pass
            
    title = p.title if getattr(p, 'title', None) else ""
    subtitle = p.categories[0] if getattr(p, 'categories', None) else (p.description[:100] if getattr(p, 'description', None) else "")
    
    price = "0"
    if getattr(p, 'price_info', None) and p.price_info.price:
        try:
            price = str(int(p.price_info.price))
        except Exception:
            price = str(p.price_info.price)
            
    image_uris = [img.uri for img in p.images if img.uri] if getattr(p, 'images', None) else []
    uri = p.uri if getattr(p, 'uri', None) else ""
    
    return {
        "productId": product_id,
        "title": title,
        "subtitle": subtitle,
        "price": price,
        "uri": uri,
        "imageUris": image_uris
    }

@mcp.tool()
async def search_products(query: str, page_size: int = 20, filter: str = None) -> str:
    """
    [RECOMMENDED FOR AI AGENTS] Search the product catalog using natural language queries.
    This tool is optimized specifically for AI agent reasoning and should be used instead of 'search_products' when an AI agent is performing the search.
    """
    client = retail_v2.SearchServiceClient()
    product_client = retail_v2.ProductServiceClient()
    serving_config = f"{get_catalog_name()}/servingConfigs/{SERVING_CONFIG}"
    
    request = retail_v2.SearchRequest(
        placement=serving_config,
        query=query,
        page_size=page_size,
        filter=filter,
        visitor_id="mcp-agent-session" # In production, pass dynamic session IDs
    )
    
    response = client.search(request=request)
    
    catalog_name = get_catalog_name()
    results = list(response.results)
    
    if not results:
        return json.dumps({"productDetails": []}, ensure_ascii=False)
        
    # Fetch full product details in parallel
    with ThreadPoolExecutor(max_workers=min(len(results), 20)) as executor:
        futures = [executor.submit(_fetch_product_details, product_client, r, catalog_name) for r in results]
        product_details = [f.result() for f in futures]
        
    return json.dumps({"productDetails": product_details}, ensure_ascii=False, indent=2)

@mcp.tool()
async def get_product_details(product_id: str) -> str:
    """
    Retrieve specific technical details, attributes, and availability for a single product ID.
    Use this when the user asks specific questions about a known product.
    """
    client = retail_v2.ProductServiceClient()
    name = f"{get_catalog_name()}/branches/default_branch/products/{product_id}"
    
    try:
        product = client.get_product(name=name)
        
        subtitle = product.categories[0] if getattr(product, 'categories', None) else (product.description[:100] if getattr(product, 'description', None) else "")
        
        price = "0"
        if getattr(product, 'price_info', None) and product.price_info.price:
            try:
                price = str(int(product.price_info.price))
            except Exception:
                price = str(product.price_info.price)
                
        image_uris = [img.uri for img in product.images if img.uri] if getattr(product, 'images', None) else []
        
        # Attributes mapping
        attributes = {}
        if getattr(product, 'attributes', None):
            for k, v in product.attributes.items():
                if v.text:
                    attributes[k] = v.text[0] if len(v.text) == 1 else list(v.text)
                elif v.numbers:
                    attributes[k] = v.numbers[0] if len(v.numbers) == 1 else list(v.numbers)

        # Rating & Reviews
        rating = None
        review = None
        
        try:
            if product.rating:
                if product.rating.average_rating != 0.0:
                    rating = product.rating.average_rating
                
                rating_count = product.rating.rating_count
                if rating_count > 0:
                    review = {
                        "count": rating_count,
                        "reviewUri": f"{product.uri}#reviews" if product.uri else ""
                    }
        except AttributeError:
            pass

        result = {
            "productId": product_id,
            "title": product.title,
            "subtitle": subtitle,
            "price": price,
            "uri": product.uri,
            "imageUris": image_uris,
            "description": product.description or "",
            "attributes": attributes,
            "rating": rating,
            "review": review
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error finding product {product_id}: {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    # Run using uvicorn when executed directly
    import uvicorn
    uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), proxy_headers=True, forwarded_allow_ips="*")