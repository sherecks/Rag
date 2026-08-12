"""
Servidor da interface Karaguá RAG.

Expõe indexar/consultar (LightRAG) e o grafo de conhecimento via HTTP/SSE
para o frontend Bun+Vite consumir.

Rodar com: venv/Scripts/python.exe -m uvicorn backend.server:app --reload --port 8000
"""

import json
import logging
import os

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lightrag import QueryParam

from backend.auth import (
    SESSION_COOKIE_NAME,
    check_credentials,
    create_session,
    destroy_session,
    is_valid_session,
    require_auth,
)
from backend.graph_export import build_graph_data, GRAPHML_PATH
from backend.rag_service import get_rag
from backend.indexing_service import index_files, save_upload

logger = logging.getLogger("karagua.server")

app = FastAPI(title="Karaguá RAG API")

# Frontend roda no Vite dev server (porta padrão 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


class LoginBody(BaseModel):
    email: str
    password: str


@app.post("/api/login")
async def login(body: LoginBody, response: Response):
    if not check_credentials(body.email, body.password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
    token = create_session()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return {"status": "ok"}


@app.post("/api/logout")
async def logout(request: Request, response: Response):
    destroy_session(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/me")
async def me(request: Request):
    return {"authenticated": is_valid_session(request.cookies.get(SESSION_COOKIE_NAME))}


@app.get("/api/graph", dependencies=[Depends(require_auth)])
async def get_graph(limit: int = 300):
    if not os.path.exists(GRAPHML_PATH):
        raise HTTPException(
            status_code=404,
            detail="Grafo ainda não existe. Indexe documentos pelo painel '+ Indexar documentos'.",
        )
    return build_graph_data(top_n=limit)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/api/query", dependencies=[Depends(require_auth)])
async def query_stream(q: str, mode: str = "mix"):
    async def gen():
        if not os.path.exists(GRAPHML_PATH):
            yield _sse("failed", {"message": "Base ainda não indexada. Indexe documentos primeiro."})
            return

        try:
            rag = await get_rag()
            param = QueryParam(mode=mode, stream=True)
            result = await rag.aquery_llm(q, param)
        except Exception:
            logger.exception("Falha ao consultar (q=%r, mode=%r)", q, mode)
            yield _sse("failed", {"message": "Ocorreu um erro ao processar a consulta. Tente novamente."})
            return

        if result.get("status") == "failure":
            yield _sse("failed", {"message": result.get("message", "Consulta falhou.")})
            return

        data = result.get("data") or {}
        entities = [e.get("entity_name") for e in data.get("entities", []) if e.get("entity_name")]
        relationships = [
            {"source": r.get("src_id"), "target": r.get("tgt_id")}
            for r in data.get("relationships", [])
            if r.get("src_id") and r.get("tgt_id")
        ]
        yield _sse("context", {"mode": mode, "entities": entities, "relationships": relationships})

        llm = result.get("llm_response") or {}
        try:
            if llm.get("is_streaming") and llm.get("response_iterator") is not None:
                async for chunk in llm["response_iterator"]:
                    if chunk:
                        yield _sse("delta", {"text": chunk})
            else:
                yield _sse("delta", {"text": llm.get("content") or ""})
        except Exception:
            logger.exception("Falha ao transmitir resposta (q=%r, mode=%r)", q, mode)
            yield _sse("failed", {"message": "Ocorreu um erro ao processar a consulta. Tente novamente."})
            return

        yield _sse("done", {})

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/index/upload", dependencies=[Depends(require_auth)])
async def upload_files(files: list[UploadFile] = File(...)):
    saved = []
    for f in files:
        content = await f.read()
        try:
            path = save_upload(f.filename, content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        saved.append(path)
    return {"paths": saved}


@app.get("/api/index/stream", dependencies=[Depends(require_auth)])
async def index_stream(paths: list[str] = Query(...)):
    async def gen():
        try:
            async for event in index_files(paths):
                stage = event.pop("stage")
                yield _sse(stage, event)
        except Exception:
            logger.exception("Falha ao indexar documentos: %r", paths)
            yield _sse("failed", {"message": "Falha ao indexar os documentos. Tente novamente."})

    return StreamingResponse(gen(), media_type="text/event-stream")


# Serve o frontend buildado (produção). Em dev, o Vite dev server (porta 5173)
# cuida disso e faz proxy de /api para aqui — este mount fica sem efeito.
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
