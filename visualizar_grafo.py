import json
import networkx as nx
from pyvis.network import Network

GRAPHML_PATH = "./lightrag_pdf_otimizado/graph_chunk_entity_relation.graphml"
OUTPUT_HTML  = "./grafo_karagua.html"

# Quantos nós mostrar (os mais conectados). Use None para todos (lento com 1800+)
TOP_N_NODES = 300

# ─── Karaguá Design System ────────────────────────────────────────────────────
K_SURFACE_CARBON   = "#1A2332"   # fundo principal
K_SURFACE_SHELL    = "#F7F5F0"   # quase branco / cream
K_SURFACE_FOG      = "#EBE8E2"   # hover / linha alternada
K_GREEN_BRIGHT     = "#b0b0b0"   # marca — destaque máximo
K_GREEN_MID        = "#adbc25"   # marca — estado ativo
K_GREEN_DEEP       = "#828e1a"   # marca — corpo / botão primário
K_GREEN_NATURE     = "#27AE60"   # semântico — sucesso / natureza
K_CORAL            = "#E85D4A"   # semântico — erro / destaque humano
K_TEXT_PRIMARY     = "#2C3E50"   # texto escuro
K_TEXT_SECONDARY   = "#6B7B8D"   # texto secundário
K_AMBER            = "#D4AC0D"   # derivado — financeiro
K_AMBER_DEEP       = "#A47C08"   # derivado — financeiro profundo
K_TEAL             = "#1ABC9C"   # derivado — técnico/água
K_TEAL_DEEP        = "#148F77"   # derivado — espaço físico
K_BLUE             = "#3498DB"   # derivado — digital/sistema
K_PURPLE           = "#8E44AD"   # derivado — artefato/produto
K_MUTED            = "#4A5568"   # neutro escuro para nós menos relevantes
# ─────────────────────────────────────────────────────────────────────────────

# Paleta de cores por tipo de entidade (design Karaguá)
COLOR_MAP = {
    # Organizações & Projetos — verdes da marca (protagonistas)
    "organization":      K_GREEN_BRIGHT,
    "project":           K_GREEN_MID,
    "government_entity": K_GREEN_DEEP,
    "team":              K_GREEN_BRIGHT,
    "group":             K_GREEN_MID,

    # Natureza & Meio Ambiente — verdes naturais
    "naturalspecies":    K_GREEN_NATURE,
    "species":           K_GREEN_NATURE,
    "plant":             "#1E8449",
    "creature":          "#2ECC71",
    "naturalobject":     K_TEAL,
    "geologicalfeature": K_TEAL_DEEP,

    # Pessoas — coral (destaque humano)
    "person":            K_CORAL,
    "role":              "#E8806A",
    "occupation":        "#C0392B",

    # Legal / Legislação — text-secondary
    "legislation":       K_TEXT_SECONDARY,
    "legaldocument":     K_TEXT_SECONDARY,
    "legal_doc":         K_TEXT_SECONDARY,
    "law":               "#85929E",

    # Financeiro — âmbar dourado
    "financialconcept":  K_AMBER,
    "financialprogram":  K_AMBER,
    "financialparameter":"#C8860A",
    "fund":              "#F0C040",
    "financial":         K_AMBER_DEEP,

    # Documentos / Conteúdo — cream / shell
    "document":          K_SURFACE_SHELL,
    "content":           K_SURFACE_FOG,
    "report":            "#D5D0C8",
    "data":              "#BDC3C7",

    # Conceitos & Métodos — neutro claro
    "concept":           "#95A5A6",
    "method":            "#85929E",
    "plan":              "#717D7E",
    "measure":           "#7F8C8D",
    "measurement":       "#616A6B",

    # Eventos & Atividades — âmbar quente
    "event":             "#E59866",
    "activity":          "#CA6F1E",
    "initiative":        "#D68910",
    "program":           "#A04000",

    # Técnico / Digital — azul
    "system":            K_BLUE,
    "software":          "#5DADE2",
    "artifact":          K_PURPLE,
    "equipment":         "#A569BD",
    "product":           "#8E44AD",

    # Espaço / Território — teal profundo
    "location":          "#52BE80",
    "neighborhood":      "#1E8449",
    "facility":          K_TEAL_DEEP,
    "structure":         "#117A65",
    "road":              "#0E6655",

    # Tempo — azul claro desbotado
    "time":              "#A9CCE3",
    "timeperiod":        "#7FB3D3",
    "date":              "#5499C7",

    # Outros
    "furniture":         K_MUTED,
    "other":             K_MUTED,
    "UNKNOWN":           K_MUTED,
}
DEFAULT_COLOR = K_MUTED

# Legenda: apenas os grupos principais (não todos os sub-tipos)
LEGEND_GROUPS = [
    ("Organização / Projeto",  K_GREEN_BRIGHT),
    ("Governo / Equipe",       K_GREEN_DEEP),
    ("Natureza / Espécie",     K_GREEN_NATURE),
    ("Pessoa",                 K_CORAL),
    ("Legislação / Lei",       K_TEXT_SECONDARY),
    ("Financeiro",             K_AMBER),
    ("Documento / Dado",       K_SURFACE_SHELL),
    ("Conceito / Método",      "#95A5A6"),
    ("Evento / Atividade",     "#E59866"),
    ("Sistema / Software",     K_BLUE),
    ("Território / Local",     "#52BE80"),
    ("Tempo",                  "#A9CCE3"),
    ("Outros",                 K_MUTED),
]


def get_color(entity_type: str) -> str:
    return COLOR_MAP.get(entity_type.lower(), DEFAULT_COLOR)


def hex_to_rgba(hex_color: str, alpha: float = 0.35) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(74,85,104,{alpha})"


def truncate(text: str, n: int = 140) -> str:
    return text[:n] + "…" if text and len(text) > n else (text or "")


def build_viz(top_n=TOP_N_NODES):
    print("Carregando grafo...")
    G = nx.read_graphml(GRAPHML_PATH)
    print(f"  {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    if top_n and G.number_of_nodes() > top_n:
        print(f"  Filtrando para os {top_n} nós mais conectados...")
        degrees = dict(G.degree())
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:top_n]
        G = G.subgraph(top_nodes).copy()
        print(f"  Subgrafo: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    net = Network(
        height="100vh",
        width="100%",
        bgcolor=K_SURFACE_CARBON,
        font_color=K_SURFACE_SHELL,
        notebook=False,
        directed=False,
    )
    net.set_options("""{
      "physics": {
        "solver": "barnesHut",
        "barnesHut": {
          "gravitationalConstant": -800,
          "centralGravity": 0.04,
          "springLength": 150,
          "springConstant": 0.005,
          "damping": 0.25,
          "avoidOverlap": 0.3
        },
        "stabilization": {
          "enabled": true,
          "iterations": 300,
          "fit": true,
          "updateInterval": 15
        },
        "minVelocity": 0.75
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 80
      }
    }""")

    max_deg = max(d for _, d in G.degree()) or 1

    node_data = {}
    for node_id, data in G.nodes(data=True):
        etype  = data.get("entity_type", "other").lower()
        desc   = truncate(data.get("description", ""))
        degree = G.degree(node_id)
        size   = 7 + (degree / max_deg) * 38
        label  = node_id if len(node_id) <= 28 else node_id[:26] + "…"
        color  = get_color(etype)

        node_data[node_id] = {
            "desc":   data.get("description", ""),
            "etype":  etype,
            "degree": degree,
            "color":  color,
        }

        title = (
            f'<div style="font-family:\'DM Sans\',sans-serif;max-width:260px;'
            f'background:{K_SURFACE_CARBON};color:{K_SURFACE_SHELL};'
            f'padding:10px 12px;border-radius:6px;border:1px solid #2e3d52">'
            f'<b style="color:{K_GREEN_BRIGHT};font-size:13px">{node_id}</b><br>'
            f'<span style="color:{K_TEXT_SECONDARY};font-size:11px;text-transform:uppercase;'
            f'letter-spacing:.08em">{etype}</span>'
            f'<span style="color:{K_GREEN_MID};font-size:11px;margin-left:8px">'
            f'● {degree} conexões</span><br><br>'
            f'<span style="font-size:12px;line-height:1.5;color:{K_SURFACE_FOG}">{desc}</span>'
            f'</div>'
        )

        glow = hex_to_rgba(color, 0.4)
        net.add_node(
            node_id,
            label=label,
            title=title,
            color={
                "background": color,
                "border":     color,
                "highlight":  {"background": K_GREEN_BRIGHT, "border": K_GREEN_BRIGHT},
                "hover":      {"background": K_GREEN_MID,    "border": K_GREEN_BRIGHT},
            },
            size=size,
            font={"size": 10, "color": K_SURFACE_SHELL, "face": "DM Sans, sans-serif"},
            borderWidth=0,
            borderWidthSelected=2,
            shadow={"enabled": True, "color": glow, "size": 14, "x": 0, "y": 0},
        )

    for src, dst, data in G.edges(data=True):
        desc     = truncate(data.get("description", ""), 180)
        keywords = data.get("keywords", "")
        weight   = float(data.get("weight", 1.0))
        kw_html  = (
            f'<span style="color:{K_GREEN_BRIGHT};font-size:11px">{keywords}</span><br><br>'
            if keywords else ""
        )
        title = (
            f'<div style="font-family:\'DM Sans\',sans-serif;max-width:240px;'
            f'background:{K_SURFACE_CARBON};color:{K_SURFACE_SHELL};'
            f'padding:8px 11px;border-radius:6px;border:1px solid #2e3d52">'
            f'{kw_html}'
            f'<span style="font-size:12px;color:{K_SURFACE_FOG}">{desc}</span>'
            f'</div>'
        )
        net.add_edge(
            src, dst,
            title=title,
            width=0.3 + weight * 0.9,
            color={"color": "#253447", "opacity": 0.7, "highlight": "#253447", "hover": "#253447"},
            smooth={"type": "dynamic"},
        )

    node_data = {}
    for node_id, data in G.nodes(data=True):
        node_data[node_id] = {
            "desc":   data.get("description", ""),
            "etype":  data.get("entity_type", "other").lower(),
            "degree": G.degree(node_id),
            "color":  get_color(data.get("entity_type", "other").lower()),
        }

    print(f"Gerando {OUTPUT_HTML}...")
    net.save_graph(OUTPUT_HTML)
    inject_chrome(OUTPUT_HTML, node_data)
    print(f"Pronto! Abra o arquivo: {OUTPUT_HTML}")


def inject_chrome(html_path: str, node_data: dict):
    """Injeta header, legenda, painel de detalhe e estilos do design system Karaguá."""

    legend_items = "".join(
        f'<div class="leg-row">'
        f'<span class="leg-dot" style="background:{color}"></span>'
        f'<span class="leg-label">{label}</span>'
        f'</div>'
        for label, color in LEGEND_GROUPS
    )

    node_data_json = json.dumps(node_data, ensure_ascii=False)

    head_extra = f"""
<!-- Karaguá Design System chrome -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">

<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'DM Sans', sans-serif;
    background: {K_SURFACE_CARBON};
    color: {K_SURFACE_SHELL};
    overflow: hidden;
  }}
  body::before {{
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
      radial-gradient(ellipse at 25% 35%, rgba(39,174,96,0.06) 0%, transparent 55%),
      radial-gradient(ellipse at 75% 65%, rgba(52,152,219,0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 50%, rgba(26,188,156,0.03) 0%, transparent 70%);
  }}

  /* ── Canvas tela cheia ── */
  #mynetwork {{ margin-top: 0; height: 100vh !important; }}

  /* ── Legenda ── */
  #k-legend {{
    position: fixed; bottom: 20px; left: 20px; z-index: 1000;
    background: rgba(26,35,50,.92);
    border: 1px solid #2E3D52;
    border-radius: 8px;
    padding: 14px 16px;
    min-width: 192px;
    backdrop-filter: blur(8px);
    max-height: calc(100vh - 90px);
    overflow-y: auto;
  }}
  #k-legend .leg-title {{
    font-size: 11px; font-weight: 600;
    color: {K_GREEN_BRIGHT};
    text-transform: uppercase; letter-spacing: .1em;
    margin-bottom: 10px;
  }}
  .leg-row {{
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 6px;
  }}
  .leg-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    flex-shrink: 0;
  }}
  .leg-label {{
    font-size: 12px; color: {K_SURFACE_FOG};
  }}

  /* ── Painel de detalhe do nó ── */
  #k-detail {{
    position: fixed;
    top: 0; right: 0;
    width: 320px;
    height: 100vh;
    background: rgba(20,29,43,.97);
    border-left: 1px solid #2E3D52;
    backdrop-filter: blur(12px);
    z-index: 999;
    transform: translateX(100%);
    transition: transform .25s ease;
    display: flex; flex-direction: column;
    overflow: hidden;
  }}
  #k-detail.open {{ transform: translateX(0); }}

  #k-detail-header {{
    padding: 18px 18px 14px;
    border-bottom: 1px solid #2E3D52;
    flex-shrink: 0;
  }}
  #k-detail-close {{
    position: absolute; top: 14px; right: 14px;
    background: none; border: none; cursor: pointer;
    color: {K_TEXT_SECONDARY}; font-size: 18px; line-height: 1;
    padding: 2px 6px; border-radius: 4px;
    transition: color .15s, background .15s;
  }}
  #k-detail-close:hover {{ color: {K_SURFACE_SHELL}; background: #2E3D52; }}

  #k-detail-title {{
    display: flex; align-items: center; gap: 9px;
    padding-right: 28px;
  }}
  #k-detail-dot {{
    width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
  }}
  #k-detail-name {{
    font-size: 14px; font-weight: 600;
    color: {K_SURFACE_SHELL};
    word-break: break-word;
  }}
  #k-detail-meta {{
    margin-top: 8px; display: flex; align-items: center; gap: 8px;
  }}
  #k-detail-type {{
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: .1em;
    color: {K_GREEN_BRIGHT};
    background: rgba(199,217,38,.1);
    border: 1px solid rgba(199,217,38,.25);
    padding: 2px 8px; border-radius: 20px;
  }}
  #k-detail-degree {{
    font-size: 11px; color: {K_TEXT_SECONDARY};
  }}

  #k-detail-body {{
    padding: 16px 18px;
    overflow-y: auto;
    flex: 1;
  }}
  #k-detail-desc {{
    font-size: 13px; line-height: 1.65;
    color: {K_SURFACE_FOG};
    white-space: pre-wrap;
  }}

  /* ── Sobrescreve borda do pyvis / Bootstrap ── */
  #mynetwork,
  #mynetwork.card-body,
  .card,
  .card-body {{
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 0 !important;
  }}

  /* ── Loading bar: fundo escuro ── */
  #loadingBar {{ background-color: rgba(26,35,50,.92) !important; }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 4px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: #2E3D52; border-radius: 2px; }}

  /* ── Vis.js tooltip override ── */
  .vis-tooltip {{
    background: transparent !important;
    border: none !important;
    box-shadow: 0 4px 24px rgba(0,0,0,.5) !important;
    padding: 0 !important;
  }}
</style>

<script>
  const NODE_DATA = {node_data_json};
</script>

<!-- Legenda -->
<div id="k-legend">
  <div class="leg-title">Tipos de entidade</div>
  {legend_items}
</div>

<!-- Painel de detalhe -->
<div id="k-detail">
  <div id="k-detail-header">
    <button id="k-detail-close" onclick="closeDetail()">&#x2715;</button>
    <div id="k-detail-title">
      <span id="k-detail-dot"></span>
      <span id="k-detail-name"></span>
    </div>
    <div id="k-detail-meta">
      <span id="k-detail-type"></span>
      <span id="k-detail-degree"></span>
    </div>
  </div>
  <div id="k-detail-body">
    <p id="k-detail-desc"></p>
  </div>
</div>
"""

    body_extra = """
<script>
window.addEventListener('load', function() {
  if (typeof network === 'undefined') return;

  // ── Clique no nó: abre painel de detalhe ──
  network.on('click', function(params) {
    if (params.nodes.length > 0) {
      var nodeId = params.nodes[0];
      var d = NODE_DATA[nodeId];
      if (!d) return;
      document.getElementById('k-detail-name').textContent     = nodeId;
      document.getElementById('k-detail-type').textContent     = d.etype;
      document.getElementById('k-detail-degree').textContent   = d.degree + ' conexões';
      document.getElementById('k-detail-desc').textContent     = d.desc || '—';
      document.getElementById('k-detail-dot').style.background = d.color;
      document.getElementById('k-detail').classList.add('open');
    } else {
      closeDetail();
    }
  });

  // ── Edges pontilhadas no hover / seleção ──
  var _selectedNode = null;
  var _hoveredNode  = null;
  var _dashedIds    = [];

  function applyDashes(nodeId) {
    if (_dashedIds.length) {
      network.body.data.edges.update(
        _dashedIds.map(function(id) {
          return { id: id, dashes: false, color: { color: '#253447', opacity: 0.7 } };
        })
      );
      _dashedIds = [];
    }
    if (nodeId === null) return;
    _dashedIds = network.getConnectedEdges(nodeId);
    network.body.data.edges.update(
      _dashedIds.map(function(id) {
        return { id: id, dashes: [6, 4], color: { color: '#7EB8D4', opacity: 1 } };
      })
    );
  }

  network.on('selectNode',   function(p) { _selectedNode = p.nodes[0]; applyDashes(_selectedNode); });
  network.on('deselectNode', function()  { _selectedNode = null;        applyDashes(_hoveredNode);  });
  network.on('hoverNode',    function(p) { _hoveredNode  = p.node;  if (!_selectedNode) applyDashes(_hoveredNode); });
  network.on('blurNode',     function()  { _hoveredNode  = null;    if (!_selectedNode) applyDashes(null); });
});

function closeDetail() {
  document.getElementById('k-detail').classList.remove('open');
}
</script>
"""

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("</head>", head_extra + "\n</head>", 1)
    html = html.replace("</body>", body_extra + "\n</body>", 1)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    build_viz()
