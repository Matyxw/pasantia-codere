import { useState, useMemo } from 'react'
import PCCard from './PCCard'
import { IconMonitor, IconSearch } from './Icons'

export default function PCGrid({ pcs, onSelect, selectedId }) {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  const counts = useMemo(() => ({
    all:     pcs.length,
    online:  pcs.filter(p => p.status === 'online').length,
    offline: pcs.filter(p => p.status === 'offline').length,
  }), [pcs])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return pcs.filter(pc => {
      const matchFilter = filter === 'all' || pc.status === filter
      const matchSearch = !q ||
        pc.name.toLowerCase().includes(q) ||
        pc.ip.includes(q) ||
        (pc.hostname || '').toLowerCase().includes(q) ||
        (pc.os || '').toLowerCase().includes(q)
      return matchFilter && matchSearch
    })
  }, [pcs, search, filter])

  // Summary averages
  const onlinePcs  = pcs.filter(p => p.status === 'online')
  const avgCpu = (() => {
    const v = onlinePcs.filter(p => p.last_metrics?.cpu?.percent != null)
    if (!v.length) return null
    return (v.reduce((a, p) => a + p.last_metrics.cpu.percent, 0) / v.length).toFixed(1)
  })()
  const avgRam = (() => {
    const v = onlinePcs.filter(p => p.last_metrics?.memory?.percent != null)
    if (!v.length) return null
    return (v.reduce((a, p) => a + p.last_metrics.memory.percent, 0) / v.length).toFixed(1)
  })()

  if (pcs.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon"><IconMonitor size={40} /></div>
        <h3>Sin equipos registrados</h3>
        <p>Hacé click en <strong>Registrar PC</strong> para agregar la primera máquina, o usá <strong>Escanear</strong> para detectar agentes en la red.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Summary bar */}
      <div className="summary-bar">
        <div className="summary-cell">
          <div className="summary-cell-val" style={{ color: 'var(--tx-1)' }}>{counts.all}</div>
          <div className="summary-cell-lbl">Equipos</div>
        </div>
        <div className="summary-cell">
          <div className="summary-cell-val" style={{ color: 'var(--ok)' }}>{counts.online}</div>
          <div className="summary-cell-lbl">En línea</div>
        </div>
        <div className="summary-cell">
          <div className="summary-cell-val" style={{ color: counts.offline > 0 ? 'var(--err)' : 'var(--tx-4)' }}>{counts.offline}</div>
          <div className="summary-cell-lbl">Offline</div>
        </div>
        {avgCpu !== null && (
          <div className="summary-cell">
            <div className="summary-cell-val" style={{ color: avgCpu > 80 ? 'var(--err)' : 'var(--ac)' }}>{avgCpu}%</div>
            <div className="summary-cell-lbl">CPU prom.</div>
          </div>
        )}
        {avgRam !== null && (
          <div className="summary-cell">
            <div className="summary-cell-val" style={{ color: avgRam > 85 ? 'var(--err)' : '#0EA5E9' }}>{avgRam}%</div>
            <div className="summary-cell-lbl">RAM prom.</div>
          </div>
        )}
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="toolbar-title">
          Equipos monitoreados
          <span className="toolbar-count">
            ({filtered.length}{filtered.length !== pcs.length ? ` de ${pcs.length}` : ''})
          </span>
        </div>

        <div className="toolbar-right">
          <label className="search-field">
            <IconSearch size={13} style={{ flexShrink: 0 }} />
            <input
              type="text"
              placeholder="Buscar por nombre, IP, SO..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </label>

          <div className="filter-tabs">
            <button
              className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              Todas ({counts.all})
            </button>
            <button
              className={`filter-tab ${filter === 'online' ? 'active-ok' : ''}`}
              onClick={() => setFilter(filter === 'online' ? 'all' : 'online')}
            >
              Online ({counts.online})
            </button>
            <button
              className={`filter-tab ${filter === 'offline' ? 'active-err' : ''}`}
              onClick={() => setFilter(filter === 'offline' ? 'all' : 'offline')}
            >
              Offline ({counts.offline})
            </button>
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state" style={{ minHeight: 180 }}>
          <div className="empty-state-icon"><IconSearch size={28} /></div>
          <h3>Sin resultados</h3>
          <p>No se encontraron equipos con "{search}".</p>
        </div>
      ) : (
        <div className="pc-grid">
          {filtered.map(pc => (
            <PCCard
              key={pc.id}
              pc={pc}
              selected={pc.id === selectedId}
              onClick={() => onSelect(pc)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
