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

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "your-project-id")
LOCATION = os.getenv("LOCATION", "global") # Retail API is usually global
CATALOG = os.getenv("CATALOG", "default_catalog")
SERVING_CONFIG = os.getenv("SERVING_CONFIG", "default_search")

# Helper to format resource names
def get_catalog_name():
    return f"projects/{PROJECT_ID}/locations/{LOCATION}/catalogs/{CATALOG}"

@mcp.tool()
async def search_products(query: str, page_size: int = 5, filter: str = None) -> str:
    """
    Search the product catalog using natural language queries. 
    Use this for broad discovery like 'find blue running shoes' or 'summer dresses'.
    """
    client = retail_v2.SearchServiceClient()
    serving_config = f"{get_catalog_name()}/servingConfigs/{SERVING_CONFIG}"
    
    request = retail_v2.SearchRequest(
        placement=serving_config,
        query=query,
        page_size=page_size,
        filter=filter,
        visitor_id="mcp-agent-session" # In production, pass dynamic session IDs
    )
    
    response = client.search(request=request)
    
    # Format results for the LLM
    results = []
    for result in response.results:
        p = result.product
        # Note: result.id contains the actual product ID, not p.id
        product_id = result.id
        results.append(f"ID: {product_id}, Title: {p.title}, Price: {p.price_info.price}")
    
    if not results:
        return "No products found matching your query."
        
    return "\n".join(results)

@mcp.tool()
async def ai_agent_search_products(query: str, page_size: int = 5, filter: str = None) -> str:
    """
    [RECOMMENDED FOR AI AGENTS] Search the product catalog using natural language queries.
    This tool is optimized specifically for AI agent reasoning and should be used instead of 'search_products' when an AI agent is performing the search.
    """
    client = retail_v2.SearchServiceClient()
    serving_config = f"{get_catalog_name()}/servingConfigs/{SERVING_CONFIG}"
    
    request = retail_v2.SearchRequest(
        placement=serving_config,
        query=query,
        page_size=page_size,
        filter=filter,
        visitor_id="mcp-agent-session" # In production, pass dynamic session IDs
    )
    
    response = client.search(request=request)
    
    # Format results using the Agent Data Mapping schema
    product_details = []
    for result in response.results:
        p = result.product
        product_id = result.id
        
        # Mapping rules:
        # subtitle: first value of categories list if exists
        subtitle = p.categories[0] if p.categories else ""
        
        # price: string representation of price
        price = str(p.price_info.price) if p.price_info else "0.0"
        
        # imageUris: list of string URLs
        image_uris = [img.uri for img in p.images if img.uri] if p.images else []
        
        product_details.append({
            "productId": product_id,
            "title": p.title,
            "subtitle": subtitle,
            "price": price,
            "uri": p.uri,
            "imageUris": image_uris
        })
    
    if not product_details:
        return json.dumps({"productDetails": []}, ensure_ascii=False)
        
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
        return str(product) # Returns full protobuf details including attributes
    except Exception as e:
        return f"Error finding product {product_id}: {str(e)}"

@mcp.tool()
async def predict_recommendations(user_event_type: str = "detail-page-view", product_id: str = None) -> str:
    """
    Fetch ML-driven product recommendations.
    Use this when the user asks 'what goes well with this?' or 'similar items'.
    """
    client = retail_v2.PredictionServiceClient()
    # Note: Prediction requires a valid Serving Config configured for recommendations
    rec_serving_config = f"{get_catalog_name()}/servingConfigs/recently-viewed-base" 
    
    user_event = retail_v2.UserEvent(
        event_type=user_event_type,
        visitor_id="mcp-agent-session",
        product_details=[{"product": {"id": product_id}}] if product_id else []
    )

    request = retail_v2.PredictRequest(
        placement=rec_serving_config,
        user_event=user_event
    )
    
    try:
        response = client.predict(request=request)
        return "\n".join([f"Rec ID: {r.id}" for r in response.results])
    except Exception as e:
        return f"Recommendation failed: {str(e)}"

if __name__ == "__main__":
    # Run using uvicorn when executed directly
    import uvicorn
    uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), proxy_headers=True, forwarded_allow_ips="*")