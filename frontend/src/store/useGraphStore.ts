import { create } from 'zustand';
import { fetchGraph } from '../lib/api';
import type { GraphData, GraphNode } from '../lib/types';
import type { QueryContextEvent } from '../lib/queryStream';

export function linkKey(source: string, target: string): string {
  return [source, target].sort().join('|');
}

export interface Highlight {
  nodeIds: Set<string>;
  linkKeys: Set<string>;
  mode: string;
}

interface GraphStore {
  graphData: GraphData | null;
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  selectedNode: GraphNode | null;
  queryPhase: 'idle' | 'scanning' | 'streaming';
  highlight: Highlight | null;
  loadGraph: () => Promise<void>;
  selectNode: (node: GraphNode | null) => void;
  setQueryPhase: (phase: 'idle' | 'scanning' | 'streaming') => void;
  setHighlightFromContext: (ctx: QueryContextEvent) => void;
  clearHighlight: () => void;
}

export const useGraphStore = create<GraphStore>((set) => ({
  graphData: null,
  status: 'idle',
  error: null,
  selectedNode: null,
  queryPhase: 'idle',
  highlight: null,

  loadGraph: async () => {
    set({ status: 'loading', error: null });
    try {
      const graphData = await fetchGraph();
      set({ graphData, status: 'ready' });
    } catch (err) {
      set({ status: 'error', error: (err as Error).message });
    }
  },

  selectNode: (node) => set({ selectedNode: node }),

  setQueryPhase: (phase) => set({ queryPhase: phase }),

  setHighlightFromContext: (ctx) => {
    const nodeIds = new Set(ctx.entities);
    const linkKeys = new Set(ctx.relationships.map((r) => linkKey(r.source, r.target)));
    set({ highlight: { nodeIds, linkKeys, mode: ctx.mode }, queryPhase: 'streaming' });
  },

  clearHighlight: () => set({ highlight: null, queryPhase: 'idle' }),
}));
