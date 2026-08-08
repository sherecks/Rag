"""
Exporta o grafo de conhecimento do LightRAG (GraphML) para JSON, pronto para
o frontend renderizar com 3d-force-graph.

Paleta reaproveitada de context/style.css (Karaguá Design System v3.0 —
"O Estuário"): uma cor de marca em três tons, sem arco-íris de cores por tipo.
"""

import os
import time
import networkx as nx

GRAPHML_PATH = "./lightrag_pdf_otimizado/graph_chunk_entity_relation.graphml"

# ─── Karaguá Design System v3.0 (context/style.css) ──────────────────────────
K_GREEN_BRIGHT = "#c7d926"  # protagonista — natureza / pessoas
K_GREEN_MID = "#adbc25"  # institucional — organizações / eventos / sistemas
K_GREEN_DEEP = "#828e1a"  # workhorse — documentos / conceitos / demais tipos
# ───────────────────────────────────────────────────────────────────────────

TIER_BRIGHT = {
    "naturalspecies", "species", "plant", "creature", "naturalobject",
    "geologicalfeature", "person", "role", "occupation", "location",
    "neighborhood", "facility", "structure", "road",
}
TIER_MID = {
    "organization", "project", "government_entity", "team", "group",
    "system", "software", "artifact", "equipment", "product", "event",
    "activity", "initiative", "program", "financialconcept",
    "financialprogram", "financialparameter", "fund", "financial",
}
# Todo o restante (documentos, conceitos, legislação, tempo, outros) fica no
# tom "deep" (workhorse) por padrão — ver DEFAULT_COLOR.

DEFAULT_COLOR = K_GREEN_DEEP

LEGEND_GROUPS = [
    {"label": "Natureza / Pessoas", "color": K_GREEN_BRIGHT},
    {"label": "Organizações / Eventos", "color": K_GREEN_MID},
    {"label": "Documentos / Conceitos", "color": K_GREEN_DEEP},
]


def get_color(entity_type: str) -> str:
    t = (entity_type or "other").lower()
    if t in TIER_BRIGHT:
        return K_GREEN_BRIGHT
    if t in TIER_MID:
        return K_GREEN_MID
    return DEFAULT_COLOR


# Cache simples em memória: evita reler/reconstruir o GraphML a cada request.
_cache: dict[str, tuple[float, int, dict]] = {}


def build_graph_data(top_n: int | None = 300) -> dict:
    if not os.path.exists(GRAPHML_PATH):
        raise FileNotFoundError(GRAPHML_PATH)

    mtime = os.path.getmtime(GRAPHML_PATH)
    cache_key = str(top_n)
    cached = _cache.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[2]

    G = nx.read_graphml(GRAPHML_PATH)

    # Mantém só o maior componente conectado: nós/clusters isolados do grafo
    # principal ficam muito distantes no layout de força e, ao destacar um
    # subgrafo numa consulta, o zoomToFit precisa afastar demais a câmera
    # pra incluí-los — encolhendo o que realmente importa na tela.
    if G.number_of_nodes() > 0:
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()

    if top_n and G.number_of_nodes() > top_n:
        degrees = dict(G.degree())
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:top_n]
        G = G.subgraph(top_nodes).copy()

    max_deg = max((d for _, d in G.degree()), default=1) or 1

    nodes = []
    for node_id, data in G.nodes(data=True):
        etype = (data.get("entity_type") or "other").lower()
        degree = G.degree(node_id)
        nodes.append(
            {
                "id": node_id,
                "type": etype,
                "description": data.get("description", ""),
                "degree": degree,
                "size": 2 + (degree / max_deg) * 10,
                "color": get_color(etype),
            }
        )

    links = []
    for src, dst, data in G.edges(data=True):
        links.append(
            {
                "source": src,
                "target": dst,
                "description": data.get("description", ""),
                "keywords": data.get("keywords", ""),
                "weight": float(data.get("weight", 1.0)),
            }
        )

    result = {
        "nodes": nodes,
        "links": links,
        "legend": LEGEND_GROUPS,
        "generated_at": time.time(),
    }
    _cache[cache_key] = (mtime, len(nodes), result)
    return result


def invalidate_cache() -> None:
    _cache.clear()


if __name__ == "__main__":
    import json

    data = build_graph_data()
    print(json.dumps({"nodes": len(data["nodes"]), "links": len(data["links"])}))
