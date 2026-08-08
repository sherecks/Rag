"""
Inicialização compartilhada do LightRAG, usada pelo servidor web.

Reaproveita a lógica de 1_indexar.py / 2_consultar.py (funções de LLM e
embedding da OpenAI), mas com suporte a streaming real de tokens e uma
instância única (singleton) reaproveitada entre requisições.
"""

import os
import asyncio

import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv

from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc

load_dotenv()

WORKING_DIR = "./lightrag_pdf_otimizado"

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

_ALLOWED_KWARGS = {
    "temperature",
    "max_tokens",
    "top_p",
    "frequency_penalty",
    "presence_penalty",
    "stop",
    "n",
    "logit_bias",
    "user",
}


async def openai_llm_complete(prompt, system_prompt=None, history_messages=None, stream=False, **kwargs):
    history_messages = history_messages or []
    kwargs_filtrados = {k: v for k, v in kwargs.items() if k in _ALLOWED_KWARGS}

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    if stream:

        async def _stream():
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                **kwargs_filtrados,
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        return _stream()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        **kwargs_filtrados,
    )
    return response.choices[0].message.content


async def openai_embedding(texts: list[str]) -> np.ndarray:
    response = await client.embeddings.create(model="text-embedding-3-small", input=texts)
    return np.array([item.embedding for item in response.data])


_rag_instance: LightRAG | None = None
_rag_lock = asyncio.Lock()


async def get_rag() -> LightRAG:
    """Retorna a instância singleton do LightRAG, inicializando na primeira chamada."""
    global _rag_instance
    if _rag_instance is not None:
        return _rag_instance

    async with _rag_lock:
        if _rag_instance is not None:
            return _rag_instance

        os.makedirs(WORKING_DIR, exist_ok=True)

        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=openai_llm_complete,
            embedding_func=EmbeddingFunc(embedding_dim=1536, max_token_size=8192, func=openai_embedding),
        )
        await rag.initialize_storages()
        _rag_instance = rag
        return _rag_instance
