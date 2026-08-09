import { useEffect, useState } from 'react';
import { GraphCanvas } from './components/GraphCanvas';
import { Legend } from './components/Legend';
import { DetailDrawer } from './components/DetailDrawer';
import { ChatPanel } from './components/ChatPanel';
import { IndexPanel } from './components/IndexPanel';
import { LoginPage } from './components/LoginPage';
import { checkSession } from './lib/auth';
import { useGraphStore } from './store/useGraphStore';

function App() {
  const status = useGraphStore((s) => s.status);
  const error = useGraphStore((s) => s.error);
  const loadGraph = useGraphStore((s) => s.loadGraph);
  const [authStatus, setAuthStatus] = useState<'checking' | 'authenticated' | 'unauthenticated'>('checking');

  useEffect(() => {
    checkSession().then((ok) => setAuthStatus(ok ? 'authenticated' : 'unauthenticated'));
  }, []);

  useEffect(() => {
    if (authStatus === 'authenticated') loadGraph();
  }, [authStatus, loadGraph]);

  if (authStatus === 'checking') {
    return <div className="app-status">Carregando…</div>;
  }

  if (authStatus === 'unauthenticated') {
    return <LoginPage onSuccess={() => setAuthStatus('authenticated')} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <img src="/logo-1.svg" alt="Karaguá RAG" className="app-logo" />
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
