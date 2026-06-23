export default function Header({ stats, wsStatus, onRegister, onScan, apiUrl }) {
  const now = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })

  const wsLabel = wsStatus === 'open' ? 'Conectado' : wsStatus === 'connecting' ? 'Conectando...' : 'Desconectado'

  return (
    <header className="header">
      <div className="header-logo">
        <div className="header-logo-icon">🖥</div>
        <span>PC Monitor <span style={{ color: 'var(--color-accent)', fontSize: 12, fontWeight: 400 }}>v2.0</span></span>
      </div>

      <div className="header-stats">
        <div className="stat-badge total">
          <span>🖥</span>
          <span>{stats.total} PCs</span>
        </div>
        <div className="stat-badge online">
          <span>●</span>
          <span>{stats.online} Online</span>
        </div>
        {stats.offline > 0 && (
          <div className="stat-badge offline">
            <span>●</span>
            <span>{stats.offline} Offline</span>
          </div>
        )}
        {stats.unknown > 0 && (
          <div className="stat-badge unknown">
            <span>●</span>
            <span>{stats.unknown} ?</span>
          </div>
        )}
      </div>

      <div className="header-actions">
        <div className="ws-indicator">
          <div className={`ws-dot ${wsStatus}`} />
          <span>{wsLabel}</span>
        </div>

        <button className="btn" onClick={onScan} title="Escanear red">
          🔍 Escanear
        </button>

        <button className="btn btn-primary" onClick={onRegister}>
          + Registrar PC
        </button>

        <a
          href={`${apiUrl}/export/excel`}
          className="btn"
          title="Exportar a Excel"
          download
        >
          📊 Excel
        </a>
      </div>
    </header>
  )
}
