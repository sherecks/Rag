"""
Indexação de documentos via web, reaproveitando a lógica de extração de
1_indexar.py, mas expondo progresso incremental para o frontend.
"""

import hashlib
import json
import os
from typing import AsyncIterator

import pdfplumber

from backend.rag_service import get_rag, WORKING_DIR
from backend.graph_export import invalidate_cache

DOCS_FOLDER = "./pdfs"
CONTEXT_FOLDER = "./context"
ALLOWED_EXTENSIONS = {".pdf", ".md"}

# Registro dos arquivos já indexados (hash do conteúdo -> nome do arquivo).
# Fica dentro do WORKING_DIR do LightRAG por ser o único diretório persistido
# no Volume do Railway — sobrevive a redeploys/restarts.
MANIFEST_PATH = os.path.join(WORKING_DIR, "indexed_manifest.json")


def _file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _load_manifest() -> dict[str, str]:
    if not os.path.exists(MANIFEST_PATH):
        return {}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_manifest(manifest: dict[str, str]) -> None:
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _extrair_texto_pdf(pdf_path: str) -> list[str]:
    documentos = []
    filename = os.path.basename(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        for i, pagina in enumerate(pdf.pages, 1):
            texto = pagina.extract_text()
            tabelas = pagina.extract_tables()
            conteudo = f"=== {filename} - Página {i}/{total_paginas} ===\n\n"
            if texto and texto.strip():
                conteudo += texto + "\n"
            if tabelas:
                conteudo += f"\n\n--- TABELAS ({len(tabelas)}) ---\n"
                for idx, tabela in enumerate(tabelas, 1):
                    conteudo += f"\n[Tabela {idx}]\n"
                    for linha in tabela:
                        linha_limpa = [str(cell or "").strip() for cell in linha]
                        conteudo += " | ".join(linha_limpa) + "\n"
                    conteudo += "\n"
            if (texto and texto.strip()) or tabelas:
                documentos.append(conteudo)
    return documentos


def _extrair_texto_md(md_path: str) -> list[str]:
    filename = os.path.basename(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        conteudo = f.read()
    return [f"=== {filename} ===\n\n{conteudo}"]


def save_upload(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Formato não suportado: {ext}")
    folder = DOCS_FOLDER if ext == ".pdf" else CONTEXT_FOLDER
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, os.path.basename(filename))
    with open(path, "wb") as f:
        f.write(content)
    return path


async def index_files(paths: list[str]) -> AsyncIterator[dict]:
    """Extrai e indexa os arquivos informados, emitindo eventos de progresso."""
    rag = await get_rag()
    manifest = _load_manifest()

    documentos: list[tuple[str, str]] = []
    new_hashes: dict[str, str] = {}
    for path in paths:
        filename = os.path.basename(path)
        file_hash = _file_hash(path)

        if file_hash in manifest:
            yield {"stage": "skipped", "file": filename, "reason": "já indexado anteriormente"}
            continue

        ext = os.path.splitext(filename)[1].lower()
        yield {"stage": "extracting", "file": filename}

        if ext == ".pdf":
            chunks = _extrair_texto_pdf(path)
        elif ext == ".md":
            chunks = _extrair_texto_md(path)
        else:
            yield {"stage": "skipped", "file": filename, "reason": "formato não suportado"}
            continue

        documentos.extend((filename, chunk) for chunk in chunks)
        new_hashes[file_hash] = filename

    total = len(documentos)
    yield {"stage": "indexing_start", "total": total}

    for i, (filename, doc) in enumerate(documentos, 1):
        await rag.ainsert(doc)
        yield {"stage": "indexing_progress", "file": filename, "current": i, "total": total}

    if new_hashes:
        manifest.update(new_hashes)
        _save_manifest(manifest)

    invalidate_cache()
    yield {"stage": "done", "total": total}
