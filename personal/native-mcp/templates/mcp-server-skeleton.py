#!/usr/bin/env python3
"""Lightweight MCP Server template — Qdrant + fastembed for semantic memory.

Replace TOOL_LIST and call_tool() body with your own logic.
Storage: ~/.local/share/{server_name}/
"""

import os, sys, json, uuid, logging
from datetime import datetime

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("mcp-server")

SERVER_NAME = os.path.splitext(os.path.basename(__file__))[0]
STORAGE_DIR = os.path.expanduser(f"~/.local/share/{SERVER_NAME}")
os.makedirs(STORAGE_DIR, exist_ok=True)

# ── Lazy resources ──────────────────────────────────────────────────
_vector_store = None
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        log.info("fastembed loaded")
    return _embedder

def get_store():
    global _vector_store
    if _vector_store is None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        _vector_store = QdrantClient(path=os.path.join(STORAGE_DIR, "qdrant"))
        collections = [c.name for c in _vector_store.get_collections().collections]
        if "items" not in collections:
            _vector_store.create_collection(
                collection_name="items",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        log.info("Qdrant ready")
    return _vector_store

def embed(text: str) -> list:
    return list(get_embedder().embed([text]))[0].tolist()

# ── MCP server ─────────────────────────────────────────────────────
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio

server = Server(SERVER_NAME)

# TODO: Replace with your own tools
@server.list_tools()
async def list_tools():
    return [
        Tool(name="add_item", description="Add an item",
             inputSchema={"type":"object","properties":{"content":{"type":"string","description":"Content to store"}},"required":["content"]}),
        Tool(name="search_items", description="Semantic search",
             inputSchema={"type":"object","properties":{"query":{"type":"string","description":"Search query"},"limit":{"type":"integer","default":5}},"required":["query"]}),
    ]

# TODO: Replace with your own logic
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    store = get_store()
    try:
        if name == "add_item":
            vec = embed(arguments["content"])
            from qdrant_client.models import PointStruct
            store.upsert(collection_name="items", points=[PointStruct(
                id=str(uuid.uuid4()), vector=vec,
                payload={"content": arguments["content"], "created_at": datetime.now().isoformat()}
            )])
            return [TextContent(type="text", text=json.dumps({"status":"ok"}))]
        elif name == "search_items":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            vec = embed(arguments["query"])
            results = store.query_points(
                collection_name="items", query=vec,
                limit=arguments.get("limit", 5),
            )
            items = [{"id": r.id, "content": r.payload["content"], "score": round(r.score,4)} for r in results.points]
            return [TextContent(type="text", text=json.dumps(items, ensure_ascii=False))]
        else:
            return [TextContent(type="text", text=json.dumps({"error":f"Unknown: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
