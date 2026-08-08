import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { streamQuery } from '../lib/queryStream';
import { useGraphStore } from '../store/useGraphStore';

const MODES = [
  { value: 'mix', label: 'Mix', title: 'Combina grafo de conhecimento e busca vetorial. Mais completo, porém mais lento.' },
  { value: 'hybrid', label: 'Hybrid', title: 'Combina busca local e global no grafo. Bom equilíbrio entre profundidade e velocidade.' },
  { value: 'local', label: 'Local', title: 'Foca em entidades diretamente relacionadas à pergunta. Rápido e específico.' },
  { value: 'global', label: 'Global', title: 'Foca em relações e temas amplos do grafo de conhecimento.' },
  { value: 'naive', label: 'Naive', title: 'Busca vetorial simples nos trechos de texto, sem usar o grafo.' },
];

interface Message {
  id: number;
  question: string;
  mode: string;
  answer: string;
  status: 'scanning' | 'streaming' | 'done' | 'error';
  error?: string;
}

let nextId = 1;

export function ChatPanel() {
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState('mix');
  const [messages, setMessages] = useState<Message[]>([]);
  const cancelRef = useRef<(() => void) | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const setQueryPhase = useGraphStore((s) => s.setQueryPhase);
  const setHighlightFromContext = useGraphStore((s) => s.setHighlightFromContext);
  const clearHighlight = useGraphStore((s) => s.clearHighlight);

  const busy = messages.length > 0 && ['scanning', 'streaming'].includes(messages[messages.length - 1].status);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  useEffect(() => () => cancelRef.current?.(), []);

  function updateLast(patch: Partial<Message>) {
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const next = [...prev];
      next[next.length - 1] = { ...next[next.length - 1], ...patch };
      return next;
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || busy) return;

    const id = nextId++;
    setMessages((prev) => [...prev, { id, question: q, mode, answer: '', status: 'scanning' }]);
    setQuestion('');
    setQueryPhase('scanning');

    cancelRef.current = streamQuery(q, mode, {
      onContext: (ctx) => {
        setHighlightFromContext(ctx);
        updateLast({ status: 'streaming' });
      },
      onDelta: (text) => {
        setMessages((prev) => {
          if (prev.length === 0) return prev;
          const next = [...prev];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, answer: last.answer + text };
          return next;
        });
      },
      onDone: () => {
        updateLast({ status: 'done' });
        setQueryPhase('idle');
      },
      onFailed: (message) => {
        updateLast({ status: 'error', error: message });
        setQueryPhase('idle');
      },
    });
  }

  return (
    <div className="chat-panel">
      {messages.length > 0 && (
        <div className="chat-messages" ref={listRef}>
          {messages.map((m) => (
            <div className="chat-message" key={m.id}>
              <div className="chat-question">
                <span className="chat-mode-badge">{m.mode}</span>
                {m.question}
              </div>
              {m.status === 'scanning' && <div className="chat-status">escaneando o grafo…</div>}
              {m.answer && (
                <div className="chat-answer">
                  <ReactMarkdown>{m.answer}</ReactMarkdown>
                </div>
              )}
              {m.status === 'streaming' && <span className="chat-cursor" />}
              {m.status === 'error' && <div className="chat-error">{m.error}</div>}
            </div>
          ))}
        </div>
      )}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <select
          className="chat-mode-select"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          disabled={busy}
          title={MODES.find((m) => m.value === mode)?.title}
        >
          {MODES.map((m) => (
            <option key={m.value} value={m.value} title={m.title}>
              {m.label}
            </option>
          ))}
        </select>
        <input
          className="chat-input"
          type="text"
          placeholder="Pergunte algo…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={busy}
        />
        <button className="chat-clear" type="button" onClick={clearHighlight} title="Limpar destaque no grafo">
          &#x2715;
        </button>
        <button className="chat-submit" type="submit" disabled={busy || !question.trim()}>
          {busy ? '…' : 'Buscar'}
        </button>
      </form>
    </div>
  );
}
