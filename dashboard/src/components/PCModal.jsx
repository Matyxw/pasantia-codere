import { useState, useEffect, useCallback } from 'react'
import MetricsChart from './MetricsChart'
import {
  IconX, IconTrash, IconTerminal, IconBarChart, IconList,
  IconSettings, IconMonitor, IconCpu, IconMemory, IconHardDrive,
  IconUsers, IconNetwork, IconClock, IconThermometer, IconActivity,
  IconCheck, IconAlert
} from './Icons'

function fmt(n, d = 1) { return n != null ? n.toFixed(d) : '—' }
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
function fmtDown(secs) {
  if (!secs) return null
  const m = Math.floor(secs / 60), s = Math.floor(secs % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

function StatCard({ label, value, sub, colorClass, icon }) {
  return (
    <div className="info-card">
      <div className="info-card-lbl">{label}</div>
      <div className={`info-card-val ${colorClass || ''}`}>{value}</div>
      {sub && <div className="info-card-sub">{sub}</div>}
    </div>
  )
}

const TABS = [
  { id: 'overview',  label: 'Overview',  Icon: IconMonitor },
  { id: 'hardware',  label: 'Hardware',  Icon: IconCpu },
  { id: 'charts',    label: 'Gráficos',  Icon: IconBarChart },
  { id: 'processes', label: 'Procesos',  Icon: IconSettings },
  { id: 'events',    label: 'Historial', Icon: IconList },
  { id: 'terminal',  label: 'Terminal',  Icon: IconTerminal },
]

export default function PCModal({ pc, onClose, onDelete, apiUrl }) {
  const [metrics, setMetrics] = useState([])
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [pcEvents, setPcEvents] = useState([])
  const [eventsLoading, setEventsLoading] = useState(false)
  const [command, setCommand] = useState('')
  const [cmdOutput, setCmdOutput] = useState('')
  const [cmdLoading, setCmdLoading] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [tab, setTab] = useState('overview')

  const m = pc.last_metrics

  const loadMetrics = useCallback(async () => {
    try {
      const r = await fetch(`${apiUrl}/pcs/${pc.id}/metrics?limit=60`)
      setMetrics(await r.json())
    } catch { setMetrics([]) }
    finally { setMetricsLoading(false) }
  }, [apiUrl, pc.id])

  useEffect(() => {
    loadMetrics()
    const t = setInterval(loadMetrics, 30000)
    return () => clearInterval(t)
  }, [loadMetrics])

  // Update chart from WS
  useEffect(() => {
    if (!m || pc.status !== 'online') return
    const diskData = m.disk ? Object.values(m.disk) : []
    const diskPct = diskData.length ? diskData[0].percent : 0
    setMetrics(prev => [...prev, {
      timestamp: m.timestamp || new Date().toISOString(),
      cpu: m.cpu?.percent ?? 0,
      ram: m.memory?.percent ?? 0,
      disk: diskPct,
    }].slice(-60))
  }, [m?.cpu?.percent, pc.status])

  // Load events on tab open
  useEffect(() => {
    if (tab !== 'events') return
    setEventsLoading(true)
    fetch(`${apiUrl}/pcs/${pc.id}/events?limit=50`)
      .then(r => r.json())
      .then(d => setPcEvents(d))
      .catch(() => setPcEvents([]))
      .finally(() => setEventsLoading(false))
  }, [tab, apiUrl, pc.id])

  const handleCommand = async () => {
    if (!command.trim()) return
    setCmdLoading(true)
    setCmdOutput('')
    try {
      const r = await fetch(`${apiUrl}/pcs/${pc.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      })
      const d = await r.json()
      setCmdOutput(d.error ? `ERROR: ${d.error}` : (d.stdout || d.stderr || '(Sin salida)'))
    } catch (e) {
      setCmdOutput(`Error de conexión: ${e.message}`)
    } finally { setCmdLoading(false) }
  }

  const diskEntries = m?.disk ? Object.entries(m.disk) : []
  const processes   = m?.processes?.top_cpu || []

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        {/* Head */}
        <div className="modal-head">
          <div className="modal-head-title">
            <div className={`status-pill ${pc.status}`}>
              <span className="status-led" />
              {pc.status}
            </div>
            <span>{pc.name}</span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 400, color: 'var(--tx-4)' }}>
              {pc.ip}
            </span>
          </div>
          <button className="btn btn-ghost" onClick={onClose}>
            <IconX size={15} />
          </button>
        </div>

        {/* Tabs */}
        <div className="modal-tabs">
          {TABS.map(t => (
            <button
              key={t.id}
              className={`modal-tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              <t.Icon size={12} />
              {t.label}
            </button>
          ))}
        </div>

        <div className="modal-body">

          {/* ── OVERVIEW ── */}
          {tab === 'overview' && (
            <>
              <div>
                <div className="section-title">Sistema en tiempo real</div>
                <div className="info-grid">
                  <StatCard label="CPU"
                    value={m ? `${fmt(m.cpu?.percent)}%` : '—'}
                    sub={m ? `${m.cpu?.logical_cores ?? '?'} núcleos · ${fmt(m.cpu?.frequency_mhz, 0)} MHz` : ''}
                    colorClass={m?.cpu?.percent > 80 ? 'err' : 'ac'} />
                  <StatCard label="RAM"
                    value={m ? `${fmt(m.memory?.percent)}%` : '—'}
                    sub={m ? `${fmt(m.memory?.used_gb)} / ${fmt(m.memory?.total_gb)} GB` : ''}
                    colorClass={m?.memory?.percent > 85 ? 'err' : 'ac'} />
                  <StatCard label="Procesos"
                    value={m?.processes?.total ?? '—'}
                    sub="activos" colorClass="ac" />
                  <StatCard label="Conexiones"
                    value={m?.network?.connections ?? '—'}
                    sub="de red" colorClass="ac" />
                  <StatCard label="Uptime"
                    value={fmtUptime(m?.uptime_seconds)}
                    sub="desde último reinicio" />
                  <StatCard label="Último contacto"
                    value={fmtTime(pc.last_seen).split(',')[1]?.trim() || '—'}
                    sub={fmtTime(pc.last_seen).split(',')[0]} />
                </div>
              </div>

              {diskEntries.length > 0 && (
                <div>
                  <div className="section-title">Discos</div>
                  <div className="info-grid">
                    {diskEntries.map(([dev, d]) => (
                      <StatCard key={dev}
                        label={dev.replace('\\\\.\\', '').replace('\\', '')}
                        value={`${fmt(d.percent)}%`}
                        sub={`${fmt(d.used_gb)} / ${fmt(d.total_gb)} GB`}
                        colorClass={d.percent > 90 ? 'err' : 'ac'} />
                    ))}
                  </div>
                </div>
              )}

              <div>
                <div className="section-title">Información del equipo</div>
                <div className="info-grid">
                  <StatCard label="Sistema operativo" value={pc.os || '—'} />
                  <StatCard label="Hostname" value={pc.hostname || '—'} />
                  <StatCard label="IP" value={pc.ip} />
                  <StatCard label="Registrado" value={fmtTime(pc.registered_at).split(',')[0]} />
                </div>
              </div>
            </>
          )}

          {/* ── HARDWARE ── */}
          {tab === 'hardware' && (
            <>
              <div>
                <div className="section-title">Hardware y red</div>
                <div className="info-grid">
                  <StatCard label="Arquitectura"
                    value={m?.system?.architecture || 'Desconocida'}
                    sub={(m?.system?.processor || '').split(' @')[0] || 'Actualice el Agente'} />
                  {m?.battery ? (
                    <StatCard label="Batería"
                      value={`${m.battery.percent}%`}
                      sub={m.battery.power_plugged ? 'Enchufada' : 'Batería'}
                      colorClass={m.battery.percent < 20 && !m.battery.power_plugged ? 'err' : 'ac'} />
                  ) : (
                    <StatCard label="Batería" value="No detectada" sub="PC de escritorio" />
                  )}
                  {m?.swap ? (
                    <StatCard label="Swap"
                      value={`${fmt(m.swap.percent)}%`}
                      sub={`${fmt(m.swap.used_gb)} / ${fmt(m.swap.total_gb)} GB`}
                      colorClass={m.swap.percent > 80 ? 'err' : 'ac'} />
                  ) : (
                    <StatCard label="Swap" value="—" />
                  )}
                  {m?.network && (
                    <StatCard label="Tráfico total"
                      value={`${fmt((m.network.bytes_recv || 0) / 1073741824, 2)} GB`}
                      sub={`Enviado: ${fmt((m.network.bytes_sent || 0) / 1073741824, 2)} GB`} />
                  )}
                </div>
              </div>

              <div>
                <div className="section-title">Usuarios conectados</div>
                {m?.users?.length > 0 ? (
                  <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)', padding: 12 }}>
                    {m.users.map((u, i) => (
                      <div key={i} className="user-row">
                        <div className="user-avatar">
                          <IconUsers size={13} />
                        </div>
                        <div>
                          <div className="user-name">{u.name}</div>
                          <div className="user-meta">
                            Acceso: {u.host ? `Remoto (IP: ${u.host})` : 'Local (Físico)'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--tx-4)', fontSize: 13 }}>Sin usuarios activos detectados.</div>
                )}
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
                <div style={{ color: 'var(--tx-4)', fontSize: 13, textAlign: 'center', padding: 24 }}>
                  Sin datos de procesos disponibles.
                </div>
              ) : (
                <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)', overflow: 'auto' }}>
                  <table className="proc-table">
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
                          <td className="name-cell">{p.name}</td>
                          <td style={{ color: p.cpu_percent > 20 ? 'var(--err)' : 'var(--tx-2)' }}>
                            {fmt(p.cpu_percent)}%
                          </td>
                          <td>{fmt(p.memory_mb, 0)}</td>
                          <td>{p.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── HISTORIAL ── */}
          {tab === 'events' && (
            <div>
              <div className="section-title">Historial de conexiones</div>
              {eventsLoading ? (
                <div className="loading-row"><div className="spinner" /><span>Cargando historial...</span></div>
              ) : pcEvents.length === 0 ? (
                <div style={{ color: 'var(--tx-4)', fontSize: 13, textAlign: 'center', padding: 24 }}>
                  Sin eventos registrados para este equipo.
                </div>
              ) : (
                <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)', overflow: 'auto' }}>
                  <table className="proc-table">
                    <thead>
                      <tr>
                        <th>Evento</th>
                        <th>Timestamp</th>
                        <th>Downtime</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pcEvents.map((ev, i) => {
                        const isOnlineEv = (ev.type || ev.event_type) === 'online'
                        const dt = ev.downtime_seconds
                        const downStr = dt ? (dt < 60 ? `${dt}s` : `${Math.floor(dt/60)}m ${Math.floor(dt%60)}s`) : '—'
                        return (
                          <tr key={ev.id ?? i}>
                            <td style={{ fontFamily: 'Inter, sans-serif', color: isOnlineEv ? 'var(--ok)' : 'var(--err)', fontWeight: 500 }}>
                              {isOnlineEv ? 'Conexión restablecida' : 'Desconectado'}
                            </td>
                            <td>{ev.timestamp ? new Date(ev.timestamp).toLocaleString('es-AR') : '—'}</td>
                            <td style={{ color: 'var(--tx-4)' }}>{downStr}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── TERMINAL ── */}
          {tab === 'terminal' && (
            <div>
              <div className="section-title">Terminal remota</div>
              {pc.status !== 'online' ? (
                <div className="form-error">
                  <IconAlert size={13} />
                  El equipo está offline. No se pueden ejecutar comandos.
                </div>
              ) : (
                <div className="terminal-panel">
                  <div className="terminal-meta">
                    Comandos permitidos:{' '}
                    <code>dir</code> <code>tasklist</code> <code>ipconfig</code>{' '}
                    <code>systeminfo</code> <code>whoami</code> <code>hostname</code>{' '}
                    <code>netstat</code> <code>ping</code> <code>echo</code> <code>type</code>
                  </div>
                  <div className="cmd-row">
                    <input
                      className="cmd-input"
                      value={command}
                      onChange={e => setCommand(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleCommand()}
                      placeholder="Ej: ipconfig /all"
                    />
                    <button className="btn btn-primary" onClick={handleCommand} disabled={cmdLoading}>
                      {cmdLoading ? <><div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} /> Ejecutando</> : 'Ejecutar'}
                    </button>
                  </div>
                  {cmdOutput && <div className="cmd-output">{cmdOutput}</div>}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-foot">
          {!confirmDelete ? (
            <button className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
              <IconTrash size={13} />
              Eliminar equipo
            </button>
          ) : (
            <>
              <span style={{ color: 'var(--err)', fontSize: 13, flexGrow: 1 }}>
                ¿Confirmar eliminación de {pc.name}?
              </span>
              <button className="btn" onClick={() => setConfirmDelete(false)}>Cancelar</button>
              <button className="btn btn-danger" onClick={() => onDelete(pc.id)}>Confirmar</button>
            </>
          )}
          <button className="btn btn-primary" onClick={onClose} style={{ marginLeft: 'auto' }}>
            <IconCheck size={13} />
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
