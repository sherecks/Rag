import { useGraphStore } from '../store/useGraphStore';

export function DetailDrawer() {
  const node = useGraphStore((s) => s.selectedNode);
  const selectNode = useGraphStore((s) => s.selectNode);

  return (
    <div className={`k-detail ${node ? 'open' : ''}`}>
      {node && (
        <>
          <div className="k-detail-header">
            <button className="k-detail-close" onClick={() => selectNode(null)}>
              &#x2715;
            </button>
            <div className="k-detail-title">
              <span className="k-detail-dot" style={{ background: node.color }} />
              <span className="k-detail-name">{node.id}</span>
            </div>
            <div className="k-detail-meta">
              <span className="k-detail-type">{node.type}</span>
              <span className="k-detail-degree">{node.degree} conexões</span>
            </div>
          </div>
          <div className="k-detail-body">
            <p className="k-detail-desc">{node.description || '—'}</p>
          </div>
        </>
      )}
    </div>
  );
}
