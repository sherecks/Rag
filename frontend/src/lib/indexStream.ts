export async function uploadFiles(files: File[]): Promise<string[]> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const res = await fetch('/api/index/upload', { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Falha no upload (${res.status})`);
  }
  const data = await res.json();
  return data.paths as string[];
}

export interface IndexEvent {
  stage: 'extracting' | 'skipped' | 'indexing_start' | 'indexing_progress' | 'done' | 'failed';
  file?: string;
  reason?: string;
  total?: number;
  current?: number;
  message?: string;
}

export function streamIndexing(paths: string[], onEvent: (ev: IndexEvent) => void): () => void {
  const params = new URLSearchParams();
  paths.forEach((p) => params.append('paths', p));
  const es = new EventSource(`/api/index/stream?${params.toString()}`);

  const stages: IndexEvent['stage'][] = ['extracting', 'skipped', 'indexing_start', 'indexing_progress', 'done', 'failed'];
  stages.forEach((stage) => {
    es.addEventListener(stage, (ev) => {
      const data = (ev as MessageEvent).data ? JSON.parse((ev as MessageEvent).data) : {};
      onEvent({ stage, ...data });
      if (stage === 'done' || stage === 'failed') es.close();
    });
  });

  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) return;
    onEvent({ stage: 'failed', message: 'Conexão com o servidor perdida.' });
    es.close();
  };

  return () => es.close();
}
