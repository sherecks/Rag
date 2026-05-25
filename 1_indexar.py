import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
import shutil
import numpy as np
from openai import AsyncOpenAI
import pdfplumber
from dotenv import load_dotenv
import glob

# Carregar API Key do arquivo .env
load_dotenv()
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ========================================
# FUNÇÕES OPENAI
# ========================================

async def openai_llm_complete(prompt, system_prompt=None, history_messages=[], **kwargs):
    kwargs_filtrados = {k: v for k, v in kwargs.items() if k in [
        'temperature', 'max_tokens', 'top_p', 'frequency_penalty',
        'presence_penalty', 'stop', 'n', 'stream', 'logit_bias', 'user'
    ]}
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        **kwargs_filtrados
    )
    return response.choices[0].message.content

async def openai_embedding(texts: list[str]) -> np.ndarray:
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return np.array([item.embedding for item in response.data])

# ========================================
# SCRIPT PRINCIPAL DE INDEXAÇÃO
# ========================================

WORKING_DIR = "./lightrag_pdf_otimizado"
DOCS_FOLDER = "./pdfs"      # PDFs e .md avulsos
CONTEXT_FOLDER = "./context"  # Todos os .md desta pasta são indexados automaticamente

def extrair_texto_pdf(pdf_path):
    documentos = []
    filename = os.path.basename(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        print(f"Total de páginas: {total_paginas}")
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
                print(f"  ✅ Pág {i}: {len(texto or '')} chars | {len(tabelas)} tabs")
    return documentos

def extrair_texto_md(md_path):
    filename = os.path.basename(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        conteudo = f.read()
    print(f"  ✅ {len(conteudo)} chars lidos")
    return [f"=== {filename} ===\n\n{conteudo}"]

async def indexar_pdfs():
    print("="*70)
    print("🚀 LIGHTRAG - INDEXAÇÃO DE DOCUMENTOS (VSCODE)")
    print("="*70)

    # Limpar dados antigos (opcional - comente se quiser manter)
    if os.path.exists(WORKING_DIR):
        resposta = input(f"\n⚠️ A pasta {WORKING_DIR} já existe. Deseja APAGAR e reindexar? (s/n): ")
        if resposta.lower() == 's':
            shutil.rmtree(WORKING_DIR)
            print("🗑️ Dados antigos removidos.")
        else:
            print("✅ Mantendo dados existentes. Adicionando novos documentos...")

    os.makedirs(WORKING_DIR, exist_ok=True)

    print("\n🔧 Inicializando LightRAG...")

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=openai_llm_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8192,
            func=openai_embedding
        ),
        chunk_token_size=1200,
        chunk_overlap_token_size=100
    )

    await rag.initialize_storages()

    # Coloque aqui o nome do arquivo avulso a indexar (.pdf ou .md), ou deixe None para pular
    ARQUIVO_ALVO = None
    arquivos = []
    if ARQUIVO_ALVO:
        arquivos.append(os.path.join(DOCS_FOLDER, ARQUIVO_ALVO))

    # Adiciona todos os .md da pasta context automaticamente
    mds_context = sorted(glob.glob(os.path.join(CONTEXT_FOLDER, "*.md")))
    arquivos.extend(mds_context)

    if not arquivos:
        print(f"\n❌ ERRO: Nenhum arquivo encontrado.")
        print(f"👉 Defina ARQUIVO_ALVO ou coloque .md em '{CONTEXT_FOLDER}'.")
        return

    print(f"\n📂 Encontrados {len(arquivos)} arquivo(s):\n")
    for arq in arquivos:
        print(f"   • {arq}")

    documentos = []

    # Processar cada arquivo
    for arq_path in arquivos:
        filename = os.path.basename(arq_path)
        ext = os.path.splitext(filename)[1].lower()
        print(f"\n{'='*70}")
        print(f"📄 Processando: {filename}")
        print(f"{'='*70}")

        if ext == ".pdf":
            documentos.extend(extrair_texto_pdf(arq_path))
        elif ext == ".md":
            documentos.extend(extrair_texto_md(arq_path))
        else:
            print(f"  ⚠️ Formato não suportado: {ext} — pulando.")
    
    # Indexar
    print(f"\n{'='*70}")
    print(f"🔄 INDEXANDO {len(documentos)} CHUNK(S) NO LIGHTRAG")
    print(f"{'='*70}")

    for i, doc in enumerate(documentos, 1):
        await rag.ainsert(doc)
        print(f"  ✅ Chunk {i}/{len(documentos)} indexado")
    
    print("\n" + "="*70)
    print("✅ INDEXAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print(f"\n💾 Dados salvos em: {WORKING_DIR}")
    print(f"👉 Agora execute o script '2_consultar.py' para fazer perguntas!")

if __name__ == "__main__":
    asyncio.run(indexar_pdfs())
