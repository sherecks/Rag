import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
WORKING_DIR = "./lightrag_pdf_otimizado"
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def openai_llm_complete(prompt, system_prompt=None, history_messages=[], **kwargs):
    kwargs_filtrados = {k:v for k,v in kwargs.items() if k in ['temperature', 'max_tokens', 'top_p']}
    messages = []
    if system_prompt: messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(model="gpt-4o-mini", messages=messages, **kwargs_filtrados)
    return response.choices[0].message.content

async def openai_embedding(texts: list[str]) -> np.ndarray:
    response = await client.embeddings.create(model="text-embedding-3-small", input=texts)
    return np.array([item.embedding for item in response.data])

async def chat_with_pdf():
    print(f"🔄 Carregando base de dados de: {WORKING_DIR}\n")
    
    if not os.path.exists(WORKING_DIR):
        print(f"❌ ERRO: A pasta '{WORKING_DIR}' não existe!")
        print("👉 Execute primeiro o script '1_indexar.py' para processar os PDFs.")
        return
    
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=openai_llm_complete,
        embedding_func=EmbeddingFunc(embedding_dim=1536, max_token_size=8192, func=openai_embedding)
    )
    
    await rag.initialize_storages()
    
    print("✅ Base carregada com sucesso!")
    print("💡 Dica: Digite 'sair' para encerrar.")
    print("-" * 70)
    
    while True:
        pergunta = input("\n❓ Sua Pergunta: ")
        
        if pergunta.lower() in ['sair', 'exit', 'quit']:
            print("👋 Encerrando chat. Até logo!")
            break
        
        if not pergunta.strip():
            continue
        
        print("⏳ Processando...")
        
        try:
            resposta = await rag.aquery(
                pergunta,
                param=QueryParam(mode="hybrid", top_k=5, enable_rerank=False)
            )
            print(f"\n💡 Resposta:\n{resposta}")
        except Exception as e:
            print(f"\n❌ Erro: {e}")
        
        print("-" * 70)

if __name__ == "__main__":
    asyncio.run(chat_with_pdf())
