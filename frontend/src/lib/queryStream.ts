export interface QueryContextEvent {
  mode: string;
  entities: string[];
  relationships: { source: string; target: string }[];
}

export interface QueryStreamHandlers {
  onContext?: (ctx: QueryContextEvent) => void;
  onDelta?: (text: string) => void;
  onDone?: () => void;
  onFailed?: (message: string) => void;
}

/** Consome /api/query via SSE. Retorna uma função para cancelar o stream. */
export function streamQuery(question: string, mode: string, handlers: QueryStreamHandlers): () => void {
  const params = new URLSearchParams({ q: question, mode });
  const es = new EventSource(`/api/query?${params.toString()}`);

  es.addEventListener('context', (ev) => {
    handlers.onContext?.(JSON.parse((ev as MessageEvent).data));
  });
  es.addEventListener('delta', (ev) => {
    handlers.onDelta?.(JSON.parse((ev as MessageEvent).data).text);
  });
  es.addEventListener('done', () => {
    handlers.onDone?.();
    es.close();
  });
  es.addEventListener('failed', (ev) => {
    const message = (ev as MessageEvent).data ? JSON.parse((ev as MessageEvent).data).message : 'Erro na consulta.';
    handlers.onFailed?.(message);
    es.close();
  });
  // Erro de conexão nativo do EventSource (não um evento nomeado nosso).
  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) return;
    handlers.onFailed?.('Conexão com o servidor perdida.');
    es.close();
  };

  return () => es.close();
}
