import { useEffect, useRef } from 'react';
import ForceGraph3D, { type ForceGraph3DInstance } from '3d-force-graph';
import { useGraphStore, linkKey, type Highlight } from '../store/useGraphStore';
import type { GraphLink, GraphNode } from '../lib/types';

const SHELL = '#f7f5f0';
const IDLE_LINK_COLOR = 'rgba(44, 62, 80, 0.18)';
const DIM_NODE_COLOR = '#d3cfc4';
const DIM_LINK_COLOR = 'rgba(44, 62, 80, 0.06)';

// Paleta categórica de context/style.css (--chart-1..4): reservada para
// distinguir o modo de consulta ativo, não para "tipos" de nó.
const MODE_ACCENT: Record<string, string> = {
  mix: '#828e1a',
  hybrid: '#adbc25',
  local: '#c7d926',
  global: '#6b7b8d',
  naive: '#1a2332',
};

const BLINK_INTERVAL_MS = 420;

function fadeTowardShell(hex: string, factor = 0.7): string {
  const h = hex.replace('#', '');
  if (h.length !== 6) return hex;
  const shell = { r: 0xf7, g: 0xf5, b: 0xf0 };
  const r = Math.round(parseInt(h.slice(0, 2), 16) * (1 - factor) + shell.r * factor);
  const g = Math.round(parseInt(h.slice(2, 4), 16) * (1 - factor) + shell.g * factor);
  const b = Math.round(parseInt(h.slice(4, 6), 16) * (1 - factor) + shell.b * factor);
  return `rgb(${r}, ${g}, ${b})`;
}

export function GraphCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<ForceGraph3DInstance<GraphNode, GraphLink> | null>(null);
  const highlightRef = useRef<Highlight | null>(null);
  const blinkOnRef = useRef(true);
  const graphData = useGraphStore((s) => s.graphData);
  const selectNode = useGraphStore((s) => s.selectNode);
  const highlight = useGraphStore((s) => s.highlight);
  const queryPhase = useGraphStore((s) => s.queryPhase);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const graph = (
      new ForceGraph3D(container, { controlType: 'orbit' }) as unknown as ForceGraph3DInstance<GraphNode, GraphLink>
    )
      .backgroundColor(SHELL)
      .nodeId('id')
      .nodeLabel((n) => `${n.id} · ${n.type}`)
      .nodeColor((n) => {
        const h = highlightRef.current;
        if (!h) return n.color;
        if (!h.nodeIds.has(n.id)) return DIM_NODE_COLOR;
        return blinkOnRef.current ? n.color : fadeTowardShell(n.color);
      })
      .nodeVal((n) => n.size)
      .nodeOpacity(1)
      .linkColor((l) => {
        const h = highlightRef.current;
        if (!h) return IDLE_LINK_COLOR;
        const src = typeof l.source === 'string' ? l.source : (l.source as unknown as GraphNode).id;
        const tgt = typeof l.target === 'string' ? l.target : (l.target as unknown as GraphNode).id;
        return h.linkKeys.has(linkKey(src, tgt)) ? MODE_ACCENT[h.mode] ?? MODE_ACCENT.hybrid : DIM_LINK_COLOR;
      })
      .linkWidth((l) => 0.2 + (l.weight ?? 1) * 0.35)
      .linkDirectionalParticles((l) => {
        const h = highlightRef.current;
        if (!h) return 0;
        const src = typeof l.source === 'string' ? l.source : (l.source as unknown as GraphNode).id;
        const tgt = typeof l.target === 'string' ? l.target : (l.target as unknown as GraphNode).id;
        return h.linkKeys.has(linkKey(src, tgt)) ? 3 : 0;
      })
      .linkDirectionalParticleSpeed(0.006)
      .linkDirectionalParticleWidth(1.6)
      .linkDirectionalParticleColor(() => {
        const h = highlightRef.current;
        return MODE_ACCENT[h?.mode ?? ''] ?? MODE_ACCENT.hybrid;
      })
      .onNodeClick((node) => selectNode(node))
      .onBackgroundClick(() => selectNode(null))
      .onNodeHover((node) => {
        container.style.cursor = node ? 'pointer' : 'default';
      });

    const controls = graph.controls() as { autoRotate: boolean; autoRotateSpeed: number };
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.2;

    graphRef.current = graph;

    const handleResize = () => graph.width(container.clientWidth).height(container.clientHeight);
    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      graph._destructor();
      container.innerHTML = '';
      graphRef.current = null;
    };
  }, [selectNode]);

  useEffect(() => {
    if (graphRef.current && graphData) {
      graphRef.current.graphData({ nodes: graphData.nodes, links: graphData.links });
    }
  }, [graphData]);

  useEffect(() => {
    highlightRef.current = highlight;
    const graph = graphRef.current;
    if (!graph) return;
    graph.refresh();
    if (highlight && highlight.nodeIds.size > 0) {
      graph.zoomToFit(1000, 30, (n) => highlight.nodeIds.has(n.id));
    }
  }, [highlight]);

  // Pisca os nós destacados enquanto a consulta está sendo processada.
  useEffect(() => {
    const analyzing = queryPhase === 'scanning' || queryPhase === 'streaming';
    if (!analyzing) {
      blinkOnRef.current = true;
      graphRef.current?.refresh();
      return;
    }
    const id = setInterval(() => {
      blinkOnRef.current = !blinkOnRef.current;
      graphRef.current?.refresh();
    }, BLINK_INTERVAL_MS);
    return () => clearInterval(id);
  }, [queryPhase]);

  return <div ref={containerRef} className="graph-canvas" />;
}
