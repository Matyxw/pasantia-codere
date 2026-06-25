import { useState, useEffect } from 'react'
import {
  IconMonitor, IconSearch, IconPlus, IconSheet,
  IconMoon, IconSun, IconRefresh, IconCircle
} from './Icons'
import ExportModal from './ExportModal'

export default function Header({ stats, wsStatus, apiUrl, darkMode, onToggleDark }) {
  const [time, setTime] = useState(new Date())
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const timeStr = time.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const wsLabel = wsStatus === 'open' ? 'WS activo' : wsStatus === 'connecting' ? 'Conectando' : 'Sin conexión'

  return (
    <>
      <header className="header">
        <div className="header-brand">
          <div className="header-brand-logo">
            <svg width="20" height="20" viewBox="0 0 100 100" fill="none">
              <text x="50" y="76" fontFamily="Arial Black, sans-serif" fontSize="76"
                fill={darkMode ? '#ffffff' : 'var(--ac)'} fontWeight="900" textAnchor="middle">C</text>
            </svg>
          </div>
          <div className="header-brand-name" style={{ color: darkMode ? 'var(--tx-1)' : '#ffffff' }}>
            Codere <span style={{ color: darkMode ? 'var(--tx-3)' : 'rgba(255,255,255,0.8)' }}>Control Center</span>
          </div>
        </div>

        {/* Stats */}
        <div className="header-stats">
          <div className="stat-chip">
            <IconMonitor size={12} />
            {stats.total} equipos
          </div>

          {stats.online > 0 && (
            <div className="stat-chip ok">
              <span className="stat-dot" />
              {stats.online} en línea
            </div>
          )}

          {stats.offline > 0 && (
            <div className="stat-chip err">
              <span className="stat-dot" />
              {stats.offline} offline
            </div>
          )}

          {stats.unknown > 0 && (
            <div className="stat-chip warn">
              <span className="stat-dot" />
              {stats.unknown} sin estado
            </div>
          )}
        </div>

        {/* Right actions */}
        <div className="header-actions">
          <div className="header-clock">{timeStr}</div>

          <div className="ws-chip" title={`WebSocket: ${wsLabel}`}>
            <span className={`ws-led ${wsStatus}`} />
            {wsLabel}
          </div>

          <button className="btn-icon" onClick={onToggleDark} title={darkMode ? 'Modo claro' : 'Modo oscuro'}>
            {darkMode ? <IconSun size={14} /> : <IconMoon size={14} />}
          </button>



          <button
            className="btn"
            title="Exportar datos a Excel"
            onClick={() => setIsExportModalOpen(true)}
          >
            <IconSheet size={13} />
            Exportar
          </button>
        </div>
      </header>

      <ExportModal 
        isOpen={isExportModalOpen} 
        onClose={() => setIsExportModalOpen(false)} 
      />
    </>
  )
}
