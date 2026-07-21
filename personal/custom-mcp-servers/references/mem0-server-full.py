#!/usr/bin/env python3
"""Lightweight mem0 MCP Server — no LLM, no cloud, pure local.

Uses: Qdrant (vector DB) + fastembed (ONNX embeddings, ~130MB model)
Tools: add_memory, search_memories, get_memories, delete_memory, delete_all_memories, memory_stats
Storage: ~/.local/share/mem0-mcp/
"""

import os, sys, json, uuid, logging
from datetime import datetime

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("mem0-mcp")

STORAGE_DIR = os.path.expanduser("~/.local/share/mem0-mcp")
os.makedirs(STORAGE_DIR, exist_ok=True)

_vector_store = None
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        log.info("fastembed loaded: BAAI/bge-small-en-v1.5")
    return _embedder

def get_store():
    global _vector_store
    if _vector_store is None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        _vector_store = QdrantClient(path=os.path.join(STORAGE_DIR, "qdrant"))
        collections = [c.name for c in _vector_store.get_collections().collections]
        if "memories" not in collections:
            _vector_store.create_collection(
                collection_name="memories",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        log.info("Qdrant ready")
    return _vector_store

def embed(text: str) -> list:
    e = get_embedder()
    return list(e.embed([text]))[0].tolist()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio

server = Server("mem0-mcp")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="add_memory", description="保存一条记忆。用于记住用户偏好、上下文、重要信息",
             inputSchema={"type":"object","properties":{"content":{"type":"string","description":"要记住的内容"},"user_id":{"type":"string","description":"用户ID，默认hermes_user","default":"hermes_user"}},"required":["content"]}),
        Tool(name="search_memories", description="语义搜索记忆，返回最相关的结果",
             inputSchema={"type":"object","properties":{"query":{"type":"string","description":"搜索查询"},"user_id":{"type":"string","description":"用户ID过滤","default":"hermes_user"},"limit":{"type":"integer","description":"返回数量，默认5","default":5}},"required":["query"]}),
        Tool(name="get_memories", description="列出记忆（分页）",
             inputSchema={"type":"object","properties":{"user_id":{"type":"string","description":"用户ID过滤","default":"hermes_user"},"page":{"type":"integer","description":"页码，默认1","default":1},"page_size":{"type":"integer","description":"每页数量，默认20","default":20}},"required":[]}),
        Tool(name="delete_memory", description="删除一条记忆",
             inputSchema={"type":"object","properties":{"memory_id":{"type":"string","description":"记忆ID"}},"required":["memory_id"]}),
        Tool(name="delete_all_memories", description="删除某个用户的所有记忆",
             inputSchema={"type":"object","properties":{"user_id":{"type":"string","description":"用户ID","default":"hermes_user"}},"required":[]}),
        Tool(name="memory_stats", description="查看记忆统计",
             inputSchema={"type":"object","properties":{"user_id":{"type":"string","description":"用户ID过滤","default":"hermes_user"}},"required":[]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    user_id = arguments.get("user_id", "hermes_user")
    store = get_store()
    try:
        if name == "add_memory":
            vec = embed(arguments["content"])
            mem_id = str(uuid.uuid4())
            from qdrant_client.models import PointStruct
            store.upsert(
                collection_name="memories",
                points=[PointStruct(
                    id=mem_id, vector=vec,
                    payload={"content": arguments["content"], "user_id": user_id,
                             "created_at": datetime.now().isoformat()}
                )]
            )
            return [TextContent(type="text", text=json.dumps({"status":"ok","memory_id":mem_id}, ensure_ascii=False))]

        elif name == "search_memories":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            vec = embed(arguments["query"])
            results = store.query_points(
                collection_name="memories", query=vec,
                query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
                limit=arguments.get("limit", 5),
            )
            items = [{"id": r.id, "content": r.payload["content"],
                      "score": round(r.score, 4), "created_at": r.payload.get("created_at","")}
                     for r in results.points]
            return [TextContent(type="text", text=json.dumps(items, ensure_ascii=False))]

        elif name == "get_memories":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            page, page_size = arguments.get("page", 1), arguments.get("page_size", 20)
            offset = (page - 1) * page_size
            f = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])
            total = store.count(collection_name="memories", count_filter=f).count
            scroll_result = store.scroll(collection_name="memories", scroll_filter=f, limit=page_size, offset=offset)
            items = [{"id": p.id, "content": p.payload["content"], "created_at": p.payload.get("created_at","")}
                     for p in scroll_result[0]]
            return [TextContent(type="text", text=json.dumps({"total":total,"page":page,"page_size":page_size,"memories":items}, ensure_ascii=False))]

        elif name == "delete_memory":
            store.delete(collection_name="memories", points_selector=[arguments["memory_id"]])
            return [TextContent(type="text", text=json.dumps({"status":"deleted","memory_id":arguments["memory_id"]}))]

        elif name == "delete_all_memories":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            store.delete(collection_name="memories",
                         points_selector=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]))
            return [TextContent(type="text", text=json.dumps({"status":"deleted_all","user_id":user_id}))]

        elif name == "memory_stats":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            c = store.count(collection_name="memories",
                            count_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]))
            return [TextContent(type="text", text=json.dumps({"user_id":user_id,"total_memories":c.count}, ensure_ascii=False))]

        else:
            return [TextContent(type="text", text=json.dumps({"error":f"Unknown: {name}"}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error":f"{type(e).__name__}: {e}"}, ensure_ascii=False))]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
