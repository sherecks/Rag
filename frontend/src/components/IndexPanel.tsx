import { useRef, useState } from 'react';
import { uploadFiles, streamIndexing, type IndexEvent } from '../lib/indexStream';
import { useGraphStore } from '../store/useGraphStore';

function describeEvent(ev: IndexEvent): string {
  switch (ev.stage) {
    case 'extracting':
      return `Extraindo texto de ${ev.file}…`;
    case 'skipped':
      return `Ignorado: ${ev.file} (${ev.reason})`;
    case 'indexing_start':
      return `Indexando ${ev.total} trecho(s) no LightRAG…`;
    case 'indexing_progress':
      return `Indexado ${ev.current}/${ev.total} (${ev.file})`;
    case 'done':
      return `Concluído! ${ev.total} trecho(s) indexado(s). Atualizando grafo…`;
    case 'failed':
      return `Erro: ${ev.message}`;
    default:
      return '';
  }
}

export function IndexPanel() {
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadGraph = useGraphStore((s) => s.loadGraph);

  async function handleIndex() {
    if (files.length === 0 || busy) return;
    setBusy(true);
    setLog([]);
    try {
      setLog((l) => [...l, `Enviando ${files.length} arquivo(s)…`]);
      const paths = await uploadFiles(files);
      streamIndexing(paths, (ev) => {
        setLog((l) => [...l, describeEvent(ev)]);
        if (ev.stage === 'done') {
          loadGraph();
          setBusy(false);
        }
        if (ev.stage === 'failed') {
          setBusy(false);
        }
      });
    } catch (err) {
      setLog((l) => [...l, `Erro: ${(err as Error).message}`]);
      setBusy(false);
    }
  }

  return (
    <div className="index-panel">
      <button className="index-toggle" onClick={() => setOpen((v) => !v)}>
        {open ? 'Fechar' : '+ Indexar documentos'}
      </button>

      {open && (
        <div className="index-card">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.md"
            disabled={busy}
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
          {files.length > 0 && (
            <ul className="index-file-list">
              {files.map((f) => (
                <li key={f.name}>{f.name}</li>
              ))}
            </ul>
          )}
          <button className="index-submit" onClick={handleIndex} disabled={busy || files.length === 0}>
            {busy ? 'Indexando…' : 'Enviar e indexar'}
          </button>
          {log.length > 0 && (
            <div className="index-log">
              {log.map((line, i) => (
                <div key={i} className="index-log-line">
                  {line}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
