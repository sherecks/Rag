import { useGraphStore } from '../store/useGraphStore';

export function Legend() {
  const legend = useGraphStore((s) => s.graphData?.legend);
  if (!legend) return null;

  return (
    <div className="k-legend">
      <div className="k-legend-title">Tipos de entidade</div>
      {legend.map((item) => (
        <div className="k-legend-row" key={item.label}>
          <span className="k-legend-dot" style={{ background: item.color }} />
          <span className="k-legend-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
