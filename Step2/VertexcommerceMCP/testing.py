import os
import asyncio
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_mcp_adapters.client import MultiServerMCPClient
import google.auth.transport.requests
import google.oauth2.id_token
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ── Custom Callback Handler ────────────────────────────────────────────────────
# This is what makes the model's REASONING visible between tool calls.
#
# HOW THE AGENT LOOP WORKS:
# ┌─────────────────────────────────────────────────────────────────┐
# │ 1. User query goes to the LLM                                  │
# │ 2. LLM THINKS: "I need to search for blue trekking dresses"    │  ← on_llm_end shows this
# │ 3. LLM outputs a TOOL CALL: search_products(query="...")       │  ← on_tool_start shows this
# │ 4. Tool executes and returns results                            │  ← on_tool_end shows this
# │ 5. Results go back to LLM                                      │
# │ 6. LLM THINKS: "These results don't mention pockets, let me…" │  ← on_llm_end shows this
# │ 7. LLM outputs another TOOL CALL or a FINAL ANSWER             │
# │ 8. If FINAL ANSWER → stop. If TOOL CALL → go to step 4.       │
# │                                                                 │
# │ STOP CONDITION: The agent stops when the LLM returns plain     │
# │ text (a final answer) instead of a tool call, OR when          │
# │ max_iterations is reached.                                      │
# └─────────────────────────────────────────────────────────────────┘

class ReasoningCallbackHandler(BaseCallbackHandler):
    """Callback that prints the model's reasoning (thoughts) and tool interactions."""
    
    def __init__(self):
        self.step_count = 0
    
    def on_llm_end(self, response, **kwargs):
        """Called when the LLM finishes generating. This is where we see the model's REASONING."""
        self.step_count += 1
        
        for generation_list in response.generations:
            for generation in generation_list:
                msg = generation.message if hasattr(generation, 'message') else None
                if not msg:
                    continue
                
                # Extract the model's reasoning text (the "thinking" part)
                reasoning_text = ""
                tool_calls = []
                
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, str) and msg.content.strip():
                        reasoning_text = msg.content.strip()
                    elif isinstance(msg.content, list):
                        for part in msg.content:
                            if isinstance(part, dict):
                                if part.get('type') == 'text' and part.get('text', '').strip():
                                    reasoning_text = part['text'].strip()
                
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = msg.tool_calls
                
                # Print the model's reasoning
                print(f"\n{'─' * 70}")
                print(f"🧠 MODEL REASONING (Step {self.step_count}):")
                print(f"{'─' * 70}")
                
                if reasoning_text:
                    print(f"   💭 Thought: {reasoning_text}")
                else:
                    print(f"   💭 (No explicit reasoning text — model went straight to action)")
                
                if tool_calls:
                    for tc in tool_calls:
                        print(f"   🔧 Decision: Call '{tc['name']}' with args: {tc['args']}")
                else:
                    print(f"   ✅ Decision: Provide final answer to the user")

    def on_tool_start(self, serialized, input_str, **kwargs):
        """Called when a tool starts executing."""
        tool_name = serialized.get("name", "unknown")
        print(f"\n   ⏳ Executing tool '{tool_name}'...")

    def on_tool_end(self, output, **kwargs):
        """Called when a tool finishes. Shows what data came back."""
        output_str = str(output)
        if len(output_str) > 400:
            output_str = output_str[:400] + "..."
        print(f"   📦 Result: {output_str}")


# ── Configuration ──────────────────────────────────────────────────────────────
PROJECT_ID = "retail-search-jp-demo-minsoo"
REGION = "us-central1"
CLOUD_RUN_URL = "https://mcp-commerce-for-agent-1064299839440.us-central1.run.app"

async def main():
    #user_query = "Find me a blue trekking dress for a 2 days trip and tell me if it has pockets."
    user_query = "Please tell me how to manage dry skin for men."
    
    print("=" * 70)
    print(f"👤 USER QUERY: {user_query}")
    print("=" * 70)

    # ── Step 1: Authenticate ───────────────────────────────────────────────
    print("\n📡 Connecting to MCP server...")
    auth_req = google.auth.transport.requests.Request()
    try:
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, CLOUD_RUN_URL)
        headers = {"Authorization": f"Bearer {id_token}"}
        print("   ✓ Authenticated with OIDC token")
    except Exception:
        print("   ⚠ No ID token (using unauthenticated access)")
        headers = {}

    # ── Step 2: Connect to MCP Server ──────────────────────────────────────
    client = MultiServerMCPClient({
        "commerce": {
            "url": CLOUD_RUN_URL + "/mcp",
            "transport": "streamable_http",
            "headers": headers
        }
    })

    # ── Step 3: Initialize Gemini ──────────────────────────────────────────
    #model_name = "gemini-3.5-flash"
    model_name = "gemini-3-flash-preview"
    print(f"   ✓ Using model: {model_name}")
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        project=PROJECT_ID,
        temperature=0
    )

    # ── Step 4: Discover Tools ─────────────────────────────────────────────
    tools = await client.get_tools()
    print(f"   ✓ Discovered {len(tools)} tools: {[t.name for t in tools]}")

    # ── Step 5: Build the Agent ────────────────────────────────────────────
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful shopping assistant. Use the provided tools to search for products and answer questions based on the catalog data.

IMPORTANT GUIDELINES:
1. Always prefer using 'ai_agent_search_products' over 'search_products' for searching the product catalog.
2. Break the user's question into sub-tasks (e.g., find dress → check if it has pockets).
3. Search once or twice, then use 'get_product_details' on the most relevant IDs.
4. Do NOT keep searching with minor query variations. After 2 searches, work with what you have.
5. If the catalog doesn't have an exact match, recommend the closest alternatives.
6. Always end with a clear, helpful final answer summarizing your findings."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    
    reasoning_handler = ReasoningCallbackHandler()
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,                      # We use our custom handler instead
        max_iterations=8,                   # Reasonable limit
        early_stopping_method="force",   # Forces a final answer even if max iterations hit
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        callbacks=[reasoning_handler],
    )

    # ── Step 6: Run the Agent ──────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("🚀 STARTING AGENT REASONING LOOP")
    print(f"{'=' * 70}")
    
    response = await agent_executor.ainvoke(
        {"input": user_query},
        config={"callbacks": [reasoning_handler]}
    )
    
    # ── Step 7: Final Answer ───────────────────────────────────────────────
    num_steps = len(response.get("intermediate_steps", []))
    print(f"\n{'=' * 70}")
    print(f"💬 FINAL ANSWER (after {num_steps} tool calls):")
    print(f"{'=' * 70}")
    print(f"\n{response['output']}\n")

if __name__ == "__main__":
    asyncio.run(main())