import os
import asyncio
import numpy as np
from dotenv import load_dotenv
from openai import AsyncOpenAI
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from typing import Optional
import chainlit as cl

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORKING_DIR = "./lightrag_pdf_otimizado"

if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ==========================
# FUNÇÕES DO LIGHTRAG
# ==========================

async def openai_llm_complete(prompt, system_prompt=None, history_messages=None, **kwargs):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    resp = await client.chat.completions.create(
        model="o3",
        messages=messages,
    )
    return resp.choices[0].message.content

async def openai_embedding(texts: list[str]) -> np.ndarray:
    resp = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return np.array([item.embedding for item in resp.data])

# ==========================
# INICIALIZAÇÃO DO RAG
# ==========================

rag = None  # Variável global para segurar o RAG

@cl.on_chat_start
async def start():
    """Roda uma vez quando o usuário abre o chat"""
    global rag

    # Mensagem de carregamento
    msg = cl.Message(content="Inicializando RAG e carregando base de dados...")
    await msg.send()

    if rag is None:
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=openai_llm_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=openai_embedding,
            ),
            chunk_token_size=1200,
            chunk_overlap_token_size=100,
        )
        await rag.initialize_storages()

    msg.content = (
        "**RAG!** Antes de começar, responda algumas perguntas rápidas."
    )
    await msg.update()

    # ===== FORMULÁRIO INICIAL DE CONTEXTO =====
    tema = await cl.AskUserMessage(
        content=(
            "1) Sobre o que é sua dúvida principal?\n"
        ),
        timeout=600,
    ).send()

    objetivo = await cl.AskUserMessage(
        content=(
            "2) Você quer uma resposta mais voltada para:\n"
            "- Conceitos\n- Desenho de Política Pública\n- Implementação Prática\n"
        ),
        timeout=600,
    ).send()

    territorio = await cl.AskUserMessage(
        content=(
            "3) Sua dúvida envolve algum território específico em Balneário Barra do Sul?\n"
        ),
        timeout=600,
    ).send()

    nivel = await cl.AskUserMessage(
        content=(
            "4) Qual nível de detalhe você prefere?\n"
            "- Resumo Rápido\n- Explicação Intermediária\n- Implementação Completa"
        ),
        timeout=600,
    ).send()

    # Cada AskUserMessage retorna um dict; usamos .get("output", ...) para pegar o texto
    cl.user_session.set("tema_principal", tema.get("output", "PSA em geral"))
    cl.user_session.set("objetivo", objetivo.get("output", "explicação geral"))
    cl.user_session.set("territorio", territorio.get("output", "Balneário Barra do Sul"))
    cl.user_session.set("nivel_detalhe", nivel.get("output", "explicação intermediária"))

    # Inicializa histórico vazio
    cl.user_session.set("historico", [])

    await cl.Message(
        content="Obrigado! Agora pode descrever sua dúvida."
    ).send()

# ==========================
# O CHAT COM VISUALIZAÇÃO DE STEPS + MEMÓRIA
# ==========================

@cl.on_message
async def main(message: cl.Message):
    """Roda toda vez que o usuário manda uma mensagem"""

    # Recupera contexto do formulário
    tema_principal = cl.user_session.get("tema_principal") or "PSA em geral"
    objetivo = cl.user_session.get("objetivo") or "explicação geral"
    territorio = cl.user_session.get("territorio") or "Balneário Barra do Sul como um todo"
    nivel_detalhe = cl.user_session.get("nivel_detalhe") or "explicação intermediária"

    # Recupera histórico curto
    historico = cl.user_session.get("historico", [])

    historico_texto = ""
    for i, h in enumerate(historico, start=1):
        historico_texto += (
            f"\nInteração {i}:\n"
            f"Pergunta: {h['pergunta']}\n"
            f"Resumo da resposta: {h['resumo_resposta']}\n"
        )

    # RESUMO DE CONTEXTO QUE VAI PARA O RAG
    resumo_contexto = (
        f"Tema: {tema_principal}\n"
        f"Objetivo: {objetivo}\n"
        f"Território: {territorio}\n"
        f"Nível de detalhe: {nivel_detalhe}\n"
        f"Histórico curto:\n{historico_texto or 'Sem histórico relevante ainda.'}"
    )

    prompt_final = f"""
   Você é o assistente do **Projeto Karaguá** — uma iniciativa de restauração de manguezais, 
economia circular e capacitação comunitária em Balneário Barra do Sul, SC.

Seu papel é apoiar a equipe e a comunidade com informações precisas sobre:
- **Karaguá Vivo** (PSA, ecobarreiras 3D com PET reciclado, monitoramento CONAMA 357,
  sequestro de carbono Verra VM0033, plantio de 100ha de manguezal)
- **Laboratório Vivo Karaguá** (impressão 3D comunitária, oficinas de cultura digital,
  saberes do mangue, Lei Rouanet, Território Maria Fernanda)
- **Capacitação das 100 famílias** (pescadores, coletores de caranguejo, Guardas do Mangue,
  módulos M1–M7, certificação, monitoramento participativo)


---
CONTEXTO DO USUÁRIO:
{resumo_contexto if resumo_contexto else "Nenhum contexto de usuário fornecido ainda."}

HISTÓRICO RECENTE:
{historico_texto if historico_texto else "Sem histórico relevante ainda."}

PERGUNTA:
{message.content}
---


INSTRUÇÕES DE RESPOSTA:

1. **Responda com base na base de conhecimento do Karaguá.** Se a informação não estiver 
   disponível, diga claramente: *"Não encontrei essa informação na base do Karaguá."* — 
   explique o que está faltando e sugira como o usuário pode refinar a pergunta 
   (ex: "Você quer saber sobre a Fase 1 ou Fase 2? Sobre o plantio ou sobre as ecobarreiras?").

2. **Ancore na realidade local.** Sempre que possível, relacione a resposta ao contexto 
   de Balneário Barra do Sul: o Território Maria Fernanda, os canais do estuário, 
   as famílias de pescadores e coletores, a dinâmica de maré, o CONAMA 357.

3. **Mantenha coerência com o histórico.** Se o usuário está refinando um tema anterior, 
   aprofunde sem repetir o que já foi dito. Sinalize quando a pergunta muda de assunto.

4. **Adapte a linguagem ao interlocutor.** Se o usuário é da comunidade, use linguagem 
   acessível e exemplos práticos. Se for técnico (engenheiro, biólogo, captador de recursos), 
   use terminologia precisa e cite dados do projeto (ex: "500 kg de filamento/mês", 
   "70% de sobrevivência no mês 6", "R$ 1.740.000 em 36 meses").

5. **Nunca invente dados.** Se não tiver certeza, diga isso e indique onde o usuário 
   pode buscar a informação (ex: "Consulte o documento PSA do Karaguá Vivo, seção 4.6").
    """

    # Step visual no Chainlit
    async with cl.Step(name="Search:", type="tool") as step:
        step.input = f"Pergunta: {message.content}\n\nResumo enviado ao RAG:\n{resumo_contexto}"

        resposta_rag = await rag.aquery(
            prompt_final,
            param=QueryParam(mode="hybrid", top_k=5)
        )

        if not resposta_rag:
            resposta_rag = "Não encontrei informações relevantes na base para essa pergunta."

        step.output = "Consulta finalizada com sucesso."

    await cl.Message(content=resposta_rag).send()

    # ===== ATUALIZA MEMÓRIA / HISTÓRICO =====
    historico = cl.user_session.get("historico", [])
    historico.append(
        {
            "pergunta": message.content,
            "resumo_resposta": resposta_rag[:800],
        }
    )
    historico = historico[-5:]  # mantém só as últimas 5 interações
    cl.user_session.set("historico", historico)
