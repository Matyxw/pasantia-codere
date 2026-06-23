import { useState } from 'react'

export default function RegisterModal({ onClose, onRegister }) {
  const [ip, setIp] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!ip.trim() || !name.trim()) {
      setError('IP y nombre son requeridos')
      return
    }
    setLoading(true)
    setError('')
    try {
      await onRegister(ip.trim(), name.trim())
      onClose()
    } catch (err) {
      setError(err.message || 'Error al registrar PC')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal small-modal">
        <div className="modal-header">
          <div className="modal-title">+ Registrar nueva PC</div>
          <button className="btn btn-ghost" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Ingresá la IP y un nombre para identificar la PC en el panel.
              El agente debe estar corriendo en esa máquina.
            </div>

            <div className="form-group">
              <label className="form-label">Dirección IP</label>
              <input
                className="form-input"
                type="text"
                placeholder="Ej: 192.168.1.105"
                value={ip}
                onChange={e => setIp(e.target.value)}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label">Nombre de la PC</label>
              <input
                className="form-input"
                type="text"
                placeholder="Ej: PC-Laboratorio"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>

            {error && <div className="form-error">⚠ {error}</div>}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Registrando…</>
              ) : '+ Registrar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
