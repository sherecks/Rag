import { useEffect } from 'react';
import { GraphCanvas } from './components/GraphCanvas';
import { Legend } from './components/Legend';
import { DetailDrawer } from './components/DetailDrawer';
import { ChatPanel } from './components/ChatPanel';
import { IndexPanel } from './components/IndexPanel';
import { useGraphStore } from './store/useGraphStore';

function App() {
  const status = useGraphStore((s) => s.status);
  const error = useGraphStore((s) => s.error);
  const loadGraph = useGraphStore((s) => s.loadGraph);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Karaguá RAG</h1>
      </header>

      <IndexPanel />

      {status === 'ready' && <GraphCanvas />}
      {status === 'ready' && <DetailDrawer />}
      {status === 'ready' && (
        <div className="left-dock">
          <ChatPanel />
          <Legend />
        </div>
      )}

      {status === 'loading' && <div className="app-status">Carregando grafo de conhecimento…</div>}
      {status === 'error' && <div className="app-status">{error}</div>}
    </div>
  );
}

export default App;
