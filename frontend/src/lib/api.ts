import type { GraphData } from './types';

export async function fetchGraph(limit = 300): Promise<GraphData> {
  const res = await fetch(`/api/graph?limit=${limit}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Falha ao carregar o grafo (${res.status})`);
  }
  return res.json();
}
