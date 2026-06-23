import { useState } from 'react'
import { IconX, IconPlus, IconMonitor } from './Icons'

export default function RegisterModal({ onClose, onRegister }) {
  const [ip, setIp] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!ip.trim() || !name.trim()) { setError('IP y nombre son requeridos'); return }
    setLoading(true)
    setError('')
    try { await onRegister(ip.trim(), name.trim()); onClose() }
    catch (err) { setError(err.message || 'Error al registrar PC') }
    finally { setLoading(false) }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-sm">
        <div className="modal-head">
          <div className="modal-head-title">
            <IconPlus size={15} />
            Registrar nuevo equipo
          </div>
          <button className="btn btn-ghost" onClick={onClose}><IconX size={14} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <p className="form-hint">
              Ingresá la dirección IP y un nombre para identificar el equipo en el panel.
              El agente debe estar ejecutándose en esa máquina.
            </p>

            <div className="form-group">
              <label className="form-label">Dirección IP</label>
              <input
                className="form-input"
                type="text"
                placeholder="192.168.1.105"
                value={ip}
                onChange={e => setIp(e.target.value)}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label">Nombre del equipo</label>
              <input
                className="form-input"
                type="text"
                placeholder="PC-Laboratorio"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>

            {error && (
              <div className="form-error">
                <IconX size={12} />
                {error}
              </div>
            )}
          </div>

          <div className="modal-foot">
            <button type="button" className="btn" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading
                ? <><div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} /> Registrando…</>
                : <><IconPlus size={13} /> Registrar</>
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
