function timeAgo(iso) {
  if (!iso) return ''
  try {
    const diff = Date.now() - new Date(iso).getTime()
    const secs = Math.floor(diff / 1000)
    if (secs < 60) return `hace ${secs}s`
    const mins = Math.floor(secs / 60)
    if (mins < 60) return `hace ${mins}m`
    const hours = Math.floor(mins / 60)
    return `hace ${hours}h`
  } catch { return '' }
}

function fmtDowntime(secs) {
  if (!secs) return ''
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return m > 0 ? `offline ${m}m ${s}s` : `offline ${s}s`
}

export default function Sidebar({ events }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <div className="sidebar-title-dot" />
          Actividad en vivo
        </div>
      </div>

      <div className="sidebar-body">
        {events.length === 0 ? (
          <div className="sidebar-empty">
            <span style={{ fontSize: 28 }}>📭</span>
            <span>Sin eventos aún</span>
            <span style={{ fontSize: 11 }}>Los eventos de conexión aparecerán aquí en tiempo real</span>
          </div>
        ) : (
          events.map((ev, i) => (
            <div key={ev.id ?? i} className="event-item">
              <div className={`event-icon ${ev.event_type ?? ev.type}`}>
                {(ev.event_type ?? ev.type) === 'online' ? '🟢' : '🔴'}
              </div>
              <div className="event-content">
                <div className="event-pc">{ev.pc_name}</div>
                <div className="event-desc">
                  {(ev.event_type ?? ev.type) === 'online'
                    ? `Volvió online${ev.downtime_seconds ? ` · ${fmtDowntime(ev.downtime_seconds)}` : ''}`
                    : `Se desconectó · ${ev.ip}`
                  }
                </div>
              </div>
              <div className="event-time">{timeAgo(ev.timestamp)}</div>
            </div>
          ))
        )}
      </div>
    </aside>
  )
}
