"""
FastAPI server — provides the chat API and serves the frontend.
"""
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.rag_engine import query_rag
from backend.knowledge_builder import build_knowledge_base
from backend.crawler import crawl_all

app = FastAPI(title="生猪养殖行业分析智能体", version="1.0.0")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


class ChatRequest(BaseModel):
    message: str
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    model: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = query_rag(request.message, top_k=request.top_k)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/rebuild-knowledge")
async def rebuild():
    count = build_knowledge_base()
    return {"status": "ok", "chunks_indexed": count}


@app.post("/api/update-data")
async def update_data():
    """Crawl the web for new pig farming industry data and rebuild index."""
    try:
        crawl_results = crawl_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据抓取失败: {str(e)}")

    rebuild_count = 0
    if crawl_results["articles_saved"] > 0:
        try:
            rebuild_count = build_knowledge_base()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"知识库重建失败: {str(e)}")

    return {
        "status": "ok",
        "crawl": crawl_results,
        "chunks_indexed": rebuild_count,
    }


# Serve frontend static files
@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    # Auto-build knowledge base on startup if data exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    if os.path.exists(data_dir) and any(f.endswith(".txt") for f in os.listdir(data_dir)):
        build_knowledge_base(data_dir)
    uvicorn.run(app, host="0.0.0.0", port=8000)
