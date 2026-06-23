import { useState, useEffect, useCallback } from 'react'
import MetricsChart from './MetricsChart'

function fmt(n, decimals = 1) { return n != null ? n.toFixed(decimals) : '—' }
function fmtTime(iso) {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString('es-AR') } catch { return iso }
}
function fmtUptime(secs) {
  if (!secs) return '—'
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}
function fmtDowntime(secs) {
  if (!secs) return null
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

function StatCard({ label, value, sub, colorClass }) {
  return (
    <div className="info-card">
      <div className="info-card-label">{label}</div>
      <div className={`info-card-value ${colorClass || ''}`}>{value}</div>
      {sub && <div className="info-card-sub">{sub}</div>}
    </div>
  )
}

export default function PCModal({ pc, onClose, onDelete, apiUrl }) {
  const [metrics, setMetrics] = useState([])
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [command, setCommand] = useState('')
  const [cmdOutput, setCmdOutput] = useState('')
  const [cmdLoading, setCmdLoading] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [tab, setTab] = useState('overview') // overview | charts | processes | terminal

  const m = pc.last_metrics

  // Cargar historial de metricas
  const loadMetrics = useCallback(async () => {
    try {
      const resp = await fetch(`${apiUrl}/pcs/${pc.id}/metrics?limit=60`)
      const data = await resp.json()
      setMetrics(data)
    } catch {
      setMetrics([])
    } finally {
      setMetricsLoading(false)
    }
  }, [apiUrl, pc.id])

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 30000)
    return () => clearInterval(interval)
  }, [loadMetrics])

  // Actualizar metricas del chart cuando llegan por WS
  useEffect(() => {
    if (!m || pc.status !== 'online') return
    const diskData = m.disk ? Object.values(m.disk) : []
    const diskPct = diskData.length ? diskData[0].percent : 0
    const newPoint = {
      timestamp: m.timestamp || new Date().toISOString(),
      cpu: m.cpu?.percent ?? 0,
      ram: m.memory?.percent ?? 0,
      disk: diskPct,
    }
    setMetrics(prev => {
      const updated = [...prev, newPoint]
      return updated.slice(-60)
    })
  }, [m?.cpu?.percent, pc.status])

  const handleCommand = async () => {
    if (!command.trim()) return
    setCmdLoading(true)
    setCmdOutput('')
    try {
      const resp = await fetch(`${apiUrl}/pcs/${pc.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      })
      const data = await resp.json()
      if (data.error) {
        setCmdOutput(`ERROR: ${data.error}`)
      } else {
        setCmdOutput(data.stdout || data.stderr || '(Sin salida)')
      }
    } catch (e) {
      setCmdOutput(`Error de conexión: ${e.message}`)
    } finally {
      setCmdLoading(false)
    }
  }

  const diskEntries = m?.disk ? Object.entries(m.disk) : []
  const processes = m?.processes?.top_cpu || []

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <div className={`status-badge ${pc.status}`} style={{ fontSize: 12 }}>
              <div className="status-dot" />
              {pc.status}
            </div>
            <span>{pc.name}</span>
            <span style={{ color: 'var(--text-muted)', fontSize: 14, fontWeight: 400, fontFamily: 'JetBrains Mono, monospace' }}>
              {pc.ip}
            </span>
          </div>
          <button className="btn btn-ghost" onClick={onClose}>✕</button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', padding: '0 24px' }}>
          {[
            { id: 'overview',   label: '📊 Overview' },
            { id: 'charts',     label: '📈 Gráficos' },
            { id: 'processes',  label: '⚙️ Procesos' },
            { id: 'terminal',   label: '🖥 Terminal' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: '12px 16px',
                background: 'none',
                border: 'none',
                borderBottom: `2px solid ${tab === t.id ? 'var(--color-accent)' : 'transparent'}`,
                color: tab === t.id ? 'var(--text-primary)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: 13,
                fontFamily: 'Inter, sans-serif',
                fontWeight: tab === t.id ? 600 : 400,
                transition: 'all 0.15s ease',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="modal-body">
          {/* ── OVERVIEW ── */}
          {tab === 'overview' && (
            <>
              <div>
                <div className="section-title">Sistema</div>
                <div className="info-grid">
                  <StatCard label="CPU" value={m ? `${fmt(m.cpu?.percent)}%` : '—'}
                    sub={m ? `${m.cpu?.logical_cores} núcleos @ ${fmt(m.cpu?.frequency_mhz, 0)} MHz` : ''}
                    colorClass={m?.cpu?.percent > 80 ? 'offline' : 'accent'} />
                  <StatCard label="RAM"
                    value={m ? `${fmt(m.memory?.percent)}%` : '—'}
                    sub={m ? `${fmt(m.memory?.used_gb)} / ${fmt(m.memory?.total_gb)} GB` : ''}
                    colorClass={m?.memory?.percent > 85 ? 'offline' : 'accent'} />
                  <StatCard label="Procesos"
                    value={m?.processes?.total ?? '—'}
                    sub="activos" colorClass="accent" />
                  <StatCard label="Conexiones"
                    value={m?.network?.connections ?? '—'}
                    sub="de red" colorClass="accent" />
                  <StatCard label="Uptime"
                    value={fmtUptime(m?.uptime_seconds)}
                    sub="desde último reinicio" />
                  <StatCard label="Último visto"
                    value={fmtTime(pc.last_seen).split(',')[1]?.trim() || '—'}
                    sub={fmtTime(pc.last_seen).split(',')[0]} />
                </div>
              </div>

              {diskEntries.length > 0 && (
                <div>
                  <div className="section-title">Discos</div>
                  <div className="info-grid">
                    {diskEntries.map(([device, d]) => (
                      <StatCard key={device}
                        label={device.replace('\\\\.\\', '').replace('\\', '')}
                        value={`${fmt(d.percent)}%`}
                        sub={`${fmt(d.used_gb)} / ${fmt(d.total_gb)} GB · ${d.mountpoint}`}
                        colorClass={d.percent > 90 ? 'offline' : 'accent'} />
                    ))}
                  </div>
                </div>
              )}

              <div>
                <div className="section-title">Información del equipo</div>
                <div className="info-grid">
                  <StatCard label="SO" value={pc.os || '—'} />
                  <StatCard label="Hostname" value={pc.hostname || '—'} />
                  <StatCard label="IP" value={pc.ip} />
                  <StatCard label="Registrado" value={fmtTime(pc.registered_at).split(',')[0]} />
                </div>
              </div>
            </>
          )}

          {/* ── CHARTS ── */}
          {tab === 'charts' && (
            <MetricsChart data={metrics} loading={metricsLoading} />
          )}

          {/* ── PROCESSES ── */}
          {tab === 'processes' && (
            <div>
              <div className="section-title">Top procesos por CPU</div>
              {processes.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 24 }}>
                  Sin datos de procesos disponibles.
                </div>
              ) : (
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', overflow: 'auto' }}>
                  <table className="processes-table">
                    <thead>
                      <tr>
                        <th>PID</th>
                        <th>Nombre</th>
                        <th>CPU %</th>
                        <th>RAM (MB)</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {processes.map(p => (
                        <tr key={p.pid}>
                          <td>{p.pid}</td>
                          <td className="process-name-cell">{p.name}</td>
                          <td style={{ color: p.cpu_percent > 20 ? 'var(--color-offline)' : 'var(--text-secondary)' }}>
                            {fmt(p.cpu_percent)}%
                          </td>
                          <td>{fmt(p.memory_mb, 0)} MB</td>
                          <td>{p.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── TERMINAL ── */}
          {tab === 'terminal' && (
            <div>
              <div className="section-title">Terminal Remota</div>
              {pc.status !== 'online' ? (
                <div className="form-error">La PC está offline. No se pueden ejecutar comandos.</div>
              ) : (
                <div className="command-panel">
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                    Comandos permitidos: <code style={{ color: 'var(--color-accent)' }}>dir · tasklist · ipconfig · systeminfo · whoami · hostname · netstat · ping · echo · type</code>
                  </div>
                  <div className="command-input-row">
                    <input
                      className="command-input"
                      value={command}
                      onChange={e => setCommand(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleCommand()}
                      placeholder="Ej: ipconfig /all"
                    />
                    <button className="btn btn-primary" onClick={handleCommand} disabled={cmdLoading}>
                      {cmdLoading ? '⌛' : '▶ Ejecutar'}
                    </button>
                  </div>
                  {cmdOutput && (
                    <div className="command-output">{cmdOutput}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          {!confirmDelete ? (
            <button className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
              🗑 Eliminar PC
            </button>
          ) : (
            <>
              <span style={{ color: 'var(--color-offline)', fontSize: 13, alignSelf: 'center' }}>
                ¿Confirmar eliminación de {pc.name}?
              </span>
              <button className="btn" onClick={() => setConfirmDelete(false)}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => onDelete(pc.id)}>Confirmar</button>
            </>
          )}
          <button className="btn btn-primary" onClick={onClose} style={{ marginLeft: 'auto' }}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
