import { IconActivity, IconCircle } from './Icons'

function timeAgo(iso) {
  if (!iso) return ''
  try {
    const diff = Date.now() - new Date(iso).getTime()
    const secs = Math.floor(diff / 1000)
    if (secs < 60) return `${secs}s`
    const mins = Math.floor(secs / 60)
    if (mins < 60) return `${mins}m`
    return `${Math.floor(mins / 60)}h`
  } catch { return '' }
}

function fmtDowntime(secs) {
  if (!secs) return ''
  const m = Math.floor(secs / 60), s = Math.floor(secs % 60)
  return m > 0 ? `offline ${m}m` : `offline ${s}s`
}

export default function Sidebar({ events }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <span className="live-dot" />
        <span className="sidebar-head-title">Actividad en vivo</span>
      </div>

      <div className="sidebar-body">
        {events.length === 0 ? (
          <div className="sidebar-empty">
            <IconActivity size={28} style={{ opacity: 0.3 }} />
            <span>Sin eventos</span>
            <span style={{ fontSize: 11, color: 'var(--tx-4)' }}>
              Los eventos de conexión aparecerán aquí en tiempo real
            </span>
          </div>
        ) : (
          events.map((ev, i) => {
            const type = ev.event_type ?? ev.type
            const isOnline = type === 'online'
            return (
              <div key={ev.id ?? i} className="ev-item">
                <div className={`ev-icon ${type}`}>
                  <IconCircle size={8} style={{ color: isOnline ? 'var(--ok)' : 'var(--err)' }} />
                </div>
                <div className="ev-body">
                  <div className="ev-name">{ev.pc_name}</div>
                  <div className="ev-desc">
                    {isOnline
                      ? `Reconectado${ev.downtime_seconds ? ` · ${fmtDowntime(ev.downtime_seconds)}` : ''}`
                      : `Desconectado · ${ev.ip}`
                    }
                  </div>
                </div>
                <div className="ev-time">{timeAgo(ev.timestamp)}</div>
              </div>
            )
          })
        )}
      </div>
    </aside>
  )
}
