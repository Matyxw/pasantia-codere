import { useState, useEffect } from 'react'
import {
  IconMonitor, IconSearch, IconPlus, IconSheet,
  IconMoon, IconSun, IconRefresh, IconCircle
} from './Icons'

export default function Header({ stats, wsStatus, onRegister, onScan, apiUrl, darkMode, onToggleDark }) {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const timeStr = time.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const wsLabel = wsStatus === 'open' ? 'WS activo' : wsStatus === 'connecting' ? 'Conectando' : 'Sin conexión'

  return (
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

        <button className="btn" onClick={onScan} title="Escanear red local">
          <IconSearch size={13} />
          Escanear
        </button>

        <button className="btn btn-primary" onClick={onRegister}>
          <IconPlus size={13} />
          Registrar PC
        </button>

        <button
          className="btn"
          title="Exportar datos a Excel"
          onClick={async () => {
            try {
              if (window.pywebview && window.pywebview.api) {
                const res = await window.pywebview.api.export_excel_dialog()
                if (res.error) alert('Error al exportar: ' + res.error)
                else if (res.success) alert('Exportado con éxito a:\n' + res.filepath)
              } else {
                // Fallback si corre en navegador
                const res = await fetch(`${apiUrl}/export/excel`)
                if (!res.ok) throw new Error(`Error ${res.status}`)
                const blob = await res.blob()
                const url  = URL.createObjectURL(blob)
                const a    = document.createElement('a')
                a.href     = url
                a.download = `codere_monitor_${new Date().toISOString().slice(0,10)}.xlsx`
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
                URL.revokeObjectURL(url)
              }
            } catch (e) {
              alert('Error al exportar: ' + e.message)
            }
          }}
        >
          <IconSheet size={13} />
          Exportar
        </button>
      </div>
    </header>
  )
}
