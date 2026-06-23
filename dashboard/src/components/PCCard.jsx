function formatUptime(secs) {
  if (!secs) return null
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function formatTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return '—'
  }
}

function MetricBar({ label, value, colorClass }) {
  const pct = Math.min(Math.max(value ?? 0, 0), 100)
  return (
    <div className="metric-row">
      <span className="metric-label">{label}</span>
      <div className="metric-bar-track">
        <div
          className={`metric-bar-fill ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="metric-value">{pct.toFixed(0)}%</span>
    </div>
  )
}

export default function PCCard({ pc, selected, onClick }) {
  const m = pc.last_metrics
  const isOnline  = pc.status === 'online'
  const isOffline = pc.status === 'offline'
  const isUnknown = pc.status === 'unknown'

  const statusLabel = isOnline ? 'Online' : isOffline ? 'Offline' : 'Desconocido'

  const cpuPct  = m?.cpu?.percent ?? null
  const ramPct  = m?.memory?.percent ?? null
  const diskPct = (() => {
    if (!m?.disk) return null
    const disks = Object.values(m.disk)
    if (!disks.length) return null
    return disks[0].percent
  })()

  const uptime = m?.uptime_seconds ? formatUptime(m.uptime_seconds) : null

  return (
    <div
      className={`pc-card ${pc.status} ${selected ? 'selected' : ''}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="pc-card-header">
        <div className="pc-card-info">
          <div className="pc-card-name">{pc.name}</div>
          <div className="pc-card-ip">{pc.ip}</div>
          {pc.hostname && pc.hostname !== pc.name && (
            <div className="pc-card-hostname">{pc.hostname}</div>
          )}
        </div>
        <div className={`status-badge ${pc.status}`}>
          <div className="status-dot" />
          {statusLabel}
        </div>
      </div>

      {/* Metrics */}
      {isOnline && m ? (
        <div className="pc-card-metrics">
          <MetricBar label="CPU" value={cpuPct} colorClass="cpu" />
          <MetricBar label="RAM" value={ramPct} colorClass="ram" />
          {diskPct !== null && <MetricBar label="DSK" value={diskPct} colorClass="disk" />}
        </div>
      ) : isOffline ? (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          color: 'var(--color-offline)', fontSize: 12, padding: '8px 0'
        }}>
          <span>⚠</span>
          <span>Sin conexión{pc.last_offline ? ` desde ${formatTime(pc.last_offline)}` : ''}</span>
        </div>
      ) : (
        <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '8px 0' }}>
          Esperando primer respuesta…
        </div>
      )}

      {/* Footer */}
      <div className="pc-card-footer">
        <div className="pc-card-os">
          {pc.os ? `💻 ${pc.os.split(' ')[0]}` : '💻 —'}
          {uptime && <span style={{ marginLeft: 6, color: 'var(--text-muted)' }}>↑{uptime}</span>}
        </div>
        <div className="pc-card-lastseen">
          {isOnline ? `✓ ${formatTime(pc.last_seen)}` : pc.last_seen ? formatTime(pc.last_seen) : '—'}
        </div>
      </div>
    </div>
  )
}
