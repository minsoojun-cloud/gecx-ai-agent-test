# Vertex AI Commerce MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes **Google Cloud Vertex AI Search for Commerce (Retail API)** capabilities as tools that any MCP-compatible AI agent can use. Deploy it to Cloud Run and let LLM agents search your product catalog, fetch product details, and get ML-driven recommendations—all through natural language.

---

## Architecture

```
┌─────────────────┐       SSE/MCP        ┌─────────────────────┐       gRPC        ┌─────────────────────────┐
│  LLM Agent      │ ──────────────────▶  │  MCP Server         │ ──────────────▶  │  Vertex AI Commerce     │
│  (LangChain /   │                      │  (Cloud Run)        │                  │  (Retail API)           │
│   any MCP       │ ◀──────────────────  │                     │ ◀──────────────  │                         │
│   client)       │    Tool Results       │  server.py          │   Search/Recs    │  Search · Product ·     │
└─────────────────┘                      └─────────────────────┘                  │  Predict Services       │
                                                                                  └─────────────────────────┘
```

## Exposed MCP Tools

| Tool | Description | Key Parameters |
|---|---|---|
| `search_products` | Search the product catalog using natural language queries (e.g., *"blue running shoes"*). | `query` (str), `page_size` (int, default 5), `filter` (str, optional) |
| `get_product_details` | Retrieve full details for a specific product by its ID. | `product_id` (str) |
| `predict_recommendations` | Get ML-driven recommendations (e.g., *"similar items"*, *"what goes well with this?"*). | `user_event_type` (str, default `"detail-page-view"`), `product_id` (str, optional) |

---

## Project Structure

```
VAISC_MCP/
├── server.py           # MCP server – defines tools and serves via SSE
├── testing.py          # Example LangChain agent client
├── Dockerfile          # Container image definition
├── deploy.sh           # One-command Cloud Run deployment script
└── requirements.txt    # Python dependencies
```

---

## Prerequisites

- **Python 3.11+**
- **Google Cloud SDK** (`gcloud`) installed and authenticated
- A **GCP project** with:
  - Vertex AI Search for Commerce (Retail API) enabled
  - A product catalog ingested into the Retail API
  - Cloud Build and Cloud Run APIs enabled
- **Docker** (only needed for local container testing)

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd VAISC_MCP
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

For the **test client** (`testing.py`), you also need:

```bash
pip install langchain-mcp-adapters langchain-classic langchain-google-vertexai
```

---

## Configuration

The server reads its configuration from **environment variables**:

| Variable | Default | Description |
|---|---|---|
| `PROJECT_ID` | `your-project-id` | Your GCP project ID |
| `LOCATION` | `global` | Retail API location (usually `global`) |
| `CATALOG` | `default_catalog` | Retail API catalog name |
| `SERVING_CONFIG` | `default_search` | Search serving config name |
| `PORT` | `8080` | HTTP port for the server |

---

## Running Locally

```bash
# Set your project ID (or export as env var)
export PROJECT_ID="your-gcp-project-id"

# Ensure you are authenticated with GCP
gcloud auth application-default login

# Start the server
python server.py
```

The server will start at `http://localhost:8080` with an SSE endpoint at `/sse`.

---

## Deploying to Cloud Run

A one-command deployment script is included:

### 1. Edit `deploy.sh`

Update the `PROJECT_ID` variable and any environment variables you want to pass:

```bash
export PROJECT_ID="your-gcp-project-id"
```

### 2. Run the Deployment

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
1. Build the container image using **Cloud Build**
2. Push it to **Google Container Registry** (`gcr.io`)
3. Deploy to **Cloud Run** with the specified environment variables

The script outputs the **Service URL** on success.

---

## Using the Test Client

`testing.py` demonstrates how to connect a **LangChain agent** (powered by Gemini) to the deployed MCP server.

### 1. Configure `testing.py`

Update the following variables at the top of the file:

```python
PROJECT_ID = "your-gcp-project-id"
REGION = "us-central1"
CLOUD_RUN_URL = "https://your-cloud-run-service-url"  # From deploy.sh output
```

Update the `model_name` to a Gemini model available in your project:

```python
llm = ChatVertexAI(
    model_name="gemini-3-flash-preview",  # or gemini-1.5-pro, gemini-2.0-flash, etc.
    ...
)
```

### 2. Run the Client

```bash
python testing.py
```

The agent will:
1. Connect to the MCP server via SSE
2. Discover the available tools automatically
3. Use Gemini to reason about the user's query
4. Call the appropriate tools (search, details, recommendations)
5. Return a natural language answer

---

## Connecting Other MCP Clients

Any MCP-compatible client can connect to the server. The SSE endpoint is:

```
https://<your-cloud-run-url>/sse
```

### Example: Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "commerce": {
      "url": "https://your-cloud-run-url/sse",
      "transport": "sse"
    }
  }
}
```

### Example: Custom Python Client

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "commerce": {
        "url": "https://your-cloud-run-url/sse",
        "transport": "sse"
    }
})

tools = await client.get_tools()
# tools now contains: search_products, get_product_details, predict_recommendations
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| **421 Invalid Host header** | Ensure `enable_dns_rebinding_protection=False` is set in the `FastMCP` constructor (already configured in `server.py`). |
| **Container failed to start on Cloud Run** | Verify that `server.py` uses `mcp.sse_app()` (not `mcp.get_asgi_app()`) and binds to `0.0.0.0` on the `PORT` env var. |
| **404 Model not found (Vertex AI)** | Verify the Gemini model name is available in your project/region. Try `gemini-1.5-flash-001` or `gemini-2.0-flash`. |
| **ImportError: AgentExecutor** | Install `langchain-classic`: `pip install langchain-classic`. The `AgentExecutor` class has moved to this package in newer LangChain versions. |
| **`deploy.sh` syntax errors** | Ensure there are no trailing spaces after `\` line continuations. |

---

## License

Internal use only.
