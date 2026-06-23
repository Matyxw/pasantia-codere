import { useState, useEffect } from 'react'

export default function ScanModal({ onClose, onRegister, apiUrl, existingIPs }) {
  const [scanning, setScanning] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [registeringIP, setRegisteringIP] = useState(null)
  const [names, setNames] = useState({})

  const handleScan = async () => {
    setScanning(true)
    setResults(null)
    setError('')
    try {
      const resp = await fetch(`${apiUrl}/scan`)
      const data = await resp.json()
      setResults(data)
      // Pre-fill nombres con hostname
      const initial = {}
      data.found?.forEach(h => {
        initial[h.ip] = h.hostname || ''
      })
      setNames(initial)
    } catch (e) {
      setError('Error al escanear la red: ' + e.message)
    } finally {
      setScanning(false)
    }
  }

  useEffect(() => { handleScan() }, [])

  const handleRegister = async (ip) => {
    const name = (names[ip] || ip).trim()
    if (!name) return
    setRegisteringIP(ip)
    try {
      await onRegister(ip, name)
    } catch (e) {
      setError(e.message)
    } finally {
      setRegisteringIP(null)
    }
  }

  const newFound = results?.found?.filter(h => !existingIPs.includes(h.ip)) || []
  const alreadyReg = results?.found?.filter(h => existingIPs.includes(h.ip)) || []

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal small-modal" style={{ maxWidth: 560 }}>
        <div className="modal-header">
          <div className="modal-title">🔍 Escanear red</div>
          <button className="btn btn-ghost" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {scanning && (
            <div className="loading-row">
              <div className="spinner" />
              <span>Escaneando {results?.network || 'red local'} — puede tardar 10-20 segundos…</span>
            </div>
          )}

          {results && !scanning && (
            <>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Red: <code style={{ color: 'var(--color-accent)' }}>{results.network}</code> —
                Tu IP: <code style={{ color: 'var(--color-accent)' }}>{results.local_ip}</code> —
                Encontradas: <strong style={{ color: 'var(--text-primary)' }}>{results.total}</strong>
              </div>

              {newFound.length > 0 && (
                <>
                  <div className="section-title">Nuevas PCs con agente activo</div>
                  <div className="scan-list">
                    {newFound.map(host => (
                      <div key={host.ip} className="scan-item">
                        <div className="scan-item-info">
                          <div className="scan-item-ip">{host.ip}</div>
                          <div className="scan-item-host">{host.hostname || 'Sin hostname'}</div>
                        </div>
                        <input
                          className="form-input"
                          style={{ width: 140, marginRight: 8, fontSize: 12 }}
                          placeholder="Nombre"
                          value={names[host.ip] || ''}
                          onChange={e => setNames(prev => ({ ...prev, [host.ip]: e.target.value }))}
                        />
                        <button
                          className="btn btn-primary"
                          style={{ padding: '6px 12px', fontSize: 12 }}
                          onClick={() => handleRegister(host.ip)}
                          disabled={registeringIP === host.ip}
                        >
                          {registeringIP === host.ip ? '⌛' : '+ Agregar'}
                        </button>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {alreadyReg.length > 0 && (
                <>
                  <div className="section-title">Ya registradas</div>
                  <div className="scan-list">
                    {alreadyReg.map(host => (
                      <div key={host.ip} className="scan-item" style={{ opacity: 0.5 }}>
                        <div className="scan-item-info">
                          <div className="scan-item-ip">{host.ip}</div>
                          <div className="scan-item-host">{host.hostname}</div>
                        </div>
                        <span style={{ fontSize: 12, color: 'var(--color-online)' }}>✓ Registrada</span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {results.total === 0 && (
                <div className="pc-grid-empty" style={{ minHeight: 120 }}>
                  <span>😕</span>
                  <h3>Sin agentes encontrados</h3>
                  <p>Asegurate de que el agente esté corriendo en las PCs a monitorear.</p>
                </div>
              )}
            </>
          )}

          {error && <div className="form-error">⚠ {error}</div>}
        </div>

        <div className="modal-footer">
          <button className="btn" onClick={handleScan} disabled={scanning}>
            {scanning ? <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Escaneando</> : '🔄 Re-escanear'}
          </button>
          <button className="btn btn-primary" onClick={onClose} style={{ marginLeft: 'auto' }}>Cerrar</button>
        </div>
      </div>
    </div>
  )
}
