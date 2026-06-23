import PCCard from './PCCard'

export default function PCGrid({ pcs, onSelect, selectedId }) {
  if (pcs.length === 0) {
    return (
      <>
        <div className="pc-grid-header">
          <h2 className="pc-grid-title">Panel de Control</h2>
        </div>
        <div className="pc-grid-empty">
          <div className="pc-grid-empty-icon">🖥️</div>
          <h3>Sin PCs registradas</h3>
          <p>Hacé clic en <strong>Escanear</strong> para encontrar PCs en la red, o en <strong>+ Registrar PC</strong> para añadir una manualmente.</p>
        </div>
      </>
    )
  }

  const online  = pcs.filter(p => p.status === 'online')
  const offline = pcs.filter(p => p.status === 'offline')
  const unknown = pcs.filter(p => p.status === 'unknown')
  const sorted  = [...online, ...unknown, ...offline]

  return (
    <>
      <div className="pc-grid-header">
        <h2 className="pc-grid-title">
          Panel de Control
          <span style={{ fontSize: 13, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
            {pcs.length} PC{pcs.length !== 1 ? 's' : ''}
          </span>
        </h2>
      </div>
      <div className="pc-grid">
        {sorted.map(pc => (
          <PCCard
            key={pc.id}
            pc={pc}
            selected={pc.id === selectedId}
            onClick={() => onSelect(pc)}
          />
        ))}
      </div>
    </>
  )
}
