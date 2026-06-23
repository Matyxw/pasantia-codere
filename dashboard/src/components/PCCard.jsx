import { IconAlert, IconCircle } from './Icons'

function formatUptime(secs) {
  if (!secs) return null
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatTime(iso) {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }) }
  catch { return '—' }
}

function fmtBytes(b) {
  if (!b) return null
  if (b < 1024) return `${b}B/s`
  if (b < 1048576) return `${(b / 1024).toFixed(0)}K/s`
  return `${(b / 1048576).toFixed(1)}M/s`
}

function MetricBar({ label, value, colorClass }) {
  const pct = Math.min(Math.max(value ?? 0, 0), 100)
  const high = pct > 85
  return (
    <div className="metric-row">
      <span className="metric-lbl">{label}</span>
      <div className="metric-track">
        <div className={`metric-fill ${colorClass}${high ? ' high' : ''}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`metric-val${high ? ' high' : ''}`}>{pct.toFixed(0)}%</span>
    </div>
  )
}

import { memo } from 'react'

export default memo(function PCCard({ pc, selected, onClick }) {
  const m = pc.last_metrics
  const isOnline  = pc.status === 'online'
  const isOffline = pc.status === 'offline'

  const statusLabel = isOnline ? 'Online' : isOffline ? 'Offline' : 'Desconocido'
  const cpuPct  = m?.cpu?.percent ?? null
  const ramPct  = m?.memory?.percent ?? null
  const diskPct = (() => {
    if (!m?.disk) return null
    const d = Object.values(m.disk)
    return d.length ? d[0].percent : null
  })()

  const uptime  = m?.uptime_seconds ? formatUptime(m.uptime_seconds) : null
  const temp    = m?.temperature?.cpu_avg ?? m?.temperature?.current ?? null
  const netSent = m?.network?.bytes_sent_rate ?? null
  const netRecv = m?.network?.bytes_recv_rate ?? null
  const procs   = m?.processes?.total ?? null

  return (
    <div
      className={`pc-card ${pc.status}${selected ? ' selected' : ''}`}
      onClick={onClick}
    >
      {/* Head */}
      <div className="pc-card-head">
        <div className="pc-card-info">
          <div className="pc-card-name">{pc.name}</div>
          <div className="pc-card-ip">{pc.ip}</div>
          {pc.hostname && pc.hostname !== pc.name && (
            <div className="pc-card-host">{pc.hostname}</div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5 }}>
          <div className={`status-pill ${pc.status}`}>
            <span className="status-led" />
            {statusLabel}
          </div>
          {temp !== null && (
            <span className={`temp-badge${temp > 80 ? ' hot' : ''}`}>
              {Math.round(temp)}°C
            </span>
          )}
        </div>
      </div>

      {/* Metrics */}
      {isOnline && m ? (
        <div className="card-metrics">
          {cpuPct  !== null && <MetricBar label="CPU" value={cpuPct}  colorClass="cpu" />}
          {ramPct  !== null && <MetricBar label="RAM" value={ramPct}  colorClass="ram" />}
          {diskPct !== null && <MetricBar label="DSK" value={diskPct} colorClass="disk" />}
        </div>
      ) : isOffline ? (
        <div className="card-offline-msg">
          <IconAlert size={13} />
          Sin conexión{pc.last_offline ? ` desde ${formatTime(pc.last_offline)}` : ''}
        </div>
      ) : (
        <div className="card-waiting-msg">Esperando primer reporte…</div>
      )}

      {/* Net speed */}
      {isOnline && (netSent !== null || netRecv !== null || procs !== null) && (
        <div className="net-row">
          {netSent !== null && <span className="net-up">↑ {fmtBytes(netSent)}</span>}
          {netRecv !== null && <span className="net-down">↓ {fmtBytes(netRecv)}</span>}
          {procs !== null && (
            <span style={{ marginLeft: 'auto', color: 'var(--tx-4)' }}>{procs} proc.</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="pc-card-foot">
        <div className="card-meta">
          {pc.os ? pc.os.split(' ')[0] : '—'}
          {uptime && <span>· {uptime}</span>}
        </div>
        <div className="card-lastseen">
          {isOnline ? `${formatTime(pc.last_seen)}` : pc.last_seen ? formatTime(pc.last_seen) : '—'}
        </div>
      </div>
    </div>
  )
})
