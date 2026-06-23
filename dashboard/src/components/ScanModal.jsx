import { useState, useEffect } from 'react'
import { IconX, IconSearch, IconRefresh, IconPlus, IconCheck, IconAlert } from './Icons'

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
      const r = await fetch(`${apiUrl}/scan`)
      const data = await r.json()
      setResults(data)
      const initial = {}
      data.found?.forEach(h => { initial[h.ip] = h.hostname || '' })
      setNames(initial)
    } catch (e) { setError('Error al escanear la red: ' + e.message) }
    finally { setScanning(false) }
  }

  useEffect(() => { handleScan() }, [])

  const handleRegister = async (ip) => {
    const name = (names[ip] || ip).trim()
    if (!name) return
    setRegisteringIP(ip)
    try { await onRegister(ip, name) }
    catch (e) { setError(e.message) }
    finally { setRegisteringIP(null) }
  }

  const newFound    = results?.found?.filter(h => !existingIPs.includes(h.ip)) || []
  const alreadyReg  = results?.found?.filter(h => existingIPs.includes(h.ip)) || []

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-sm" style={{ maxWidth: 560 }}>
        <div className="modal-head">
          <div className="modal-head-title">
            <IconSearch size={15} />
            Escanear red local
          </div>
          <button className="btn btn-ghost" onClick={onClose}><IconX size={14} /></button>
        </div>

        <div className="modal-body">
          {scanning && (
            <div className="loading-row">
              <div className="spinner" />
              <span>Escaneando {results?.network || 'red local'} — puede tardar 10–20 segundos…</span>
            </div>
          )}

          {results && !scanning && (
            <>
              <div style={{ fontSize: 12, color: 'var(--tx-4)', fontFamily: 'JetBrains Mono, monospace' }}>
                Red: <strong style={{ color: 'var(--ac)' }}>{results.network}</strong>
                {' · '}IP local: <strong style={{ color: 'var(--ac)' }}>{results.local_ip}</strong>
                {' · '}Agentes encontrados: <strong style={{ color: 'var(--tx-1)' }}>{results.total}</strong>
              </div>

              {newFound.length > 0 && (
                <div>
                  <div className="section-title">Nuevos equipos con agente activo</div>
                  <div className="scan-list">
                    {newFound.map(host => (
                      <div key={host.ip} className="scan-row">
                        <div className="scan-row-info">
                          <div className="scan-row-ip">{host.ip}</div>
                          <div className="scan-row-host">{host.hostname || 'Sin hostname'}</div>
                        </div>
                        <input
                          className="form-input"
                          style={{ width: 130, fontSize: 12 }}
                          placeholder="Nombre"
                          value={names[host.ip] || ''}
                          onChange={e => setNames(prev => ({ ...prev, [host.ip]: e.target.value }))}
                        />
                        <button
                          className="btn btn-primary"
                          style={{ padding: '5px 10px', fontSize: 12, flexShrink: 0 }}
                          onClick={() => handleRegister(host.ip)}
                          disabled={registeringIP === host.ip}
                        >
                          {registeringIP === host.ip
                            ? <div className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                            : <><IconPlus size={12} /> Agregar</>
                          }
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {alreadyReg.length > 0 && (
                <div>
                  <div className="section-title">Ya registrados</div>
                  <div className="scan-list">
                    {alreadyReg.map(host => (
                      <div key={host.ip} className="scan-row" style={{ opacity: 0.55 }}>
                        <div className="scan-row-info">
                          <div className="scan-row-ip">{host.ip}</div>
                          <div className="scan-row-host">{host.hostname}</div>
                        </div>
                        <span style={{ fontSize: 12, color: 'var(--ok)', display: 'flex', alignItems: 'center', gap: 4 }}>
                          <IconCheck size={12} /> Registrado
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {results.total === 0 && (
                <div className="empty-state" style={{ minHeight: 120 }}>
                  <div className="empty-state-icon"><IconSearch size={28} /></div>
                  <h3>Sin agentes encontrados</h3>
                  <p>Asegurate de que el agente esté ejecutándose en las PCs a monitorear.</p>
                </div>
              )}
            </>
          )}

          {error && (
            <div className="form-error">
              <IconAlert size={13} />
              {error}
            </div>
          )}
        </div>

        <div className="modal-foot">
          <button className="btn" onClick={handleScan} disabled={scanning}>
            {scanning
              ? <><div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} /> Escaneando</>
              : <><IconRefresh size={13} /> Re-escanear</>
            }
          </button>
          <button className="btn btn-primary" onClick={onClose} style={{ marginLeft: 'auto' }}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
