import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { IconAlert, IconCheck } from './Icons'

// Usamos un sistema global simple para despachar eventos sin context
let toastCount = 0
const listeners = new Set()

export const toast = {
  success: (msg) => dispatch({ id: ++toastCount, type: 'success', msg }),
  error: (msg) => dispatch({ id: ++toastCount, type: 'error', msg }),
  warning: (msg) => dispatch({ id: ++toastCount, type: 'warning', msg })
}

function dispatch(t) {
  listeners.forEach(fn => fn(t))
}

export function ToastContainer() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const handler = (t) => {
      setToasts(prev => [...prev, t])
      // Auto dismiss
      setTimeout(() => {
        setToasts(prev => prev.filter(x => x.id !== t.id))
      }, 5000)
    }
    listeners.add(handler)
    return () => listeners.delete(handler)
  }, [])

  if (toasts.length === 0) return null

  return createPortal(
    <div className="toast-container" style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      zIndex: 9999
    }}>
      {toasts.map(t => (
        <div key={t.id} className={`toast-item toast-${t.type}`} style={{
          background: 'var(--bg-base)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r-md)',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          boxShadow: 'var(--sh-lg)',
          backdropFilter: 'blur(12px)',
          animation: 'slideIn 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) forwards',
          minWidth: '280px',
          color: 'var(--tx-1)'
        }}>
          {t.type === 'success' && <div style={{ color: 'var(--ok)' }}><IconCheck size={18} /></div>}
          {t.type === 'error' && <div style={{ color: 'var(--err)' }}><IconAlert size={18} /></div>}
          {t.type === 'warning' && <div style={{ color: 'var(--warn)' }}><IconAlert size={18} /></div>}
          
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '13px', fontWeight: 600 }}>
              {t.type === 'success' ? 'Conexión Establecida' : t.type === 'error' ? 'Alerta Crítica' : 'Advertencia'}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--tx-3)', marginTop: '2px' }}>{t.msg}</span>
          </div>
          
          <div style={{
            position: 'absolute',
            left: 0, top: 0, bottom: 0, width: '4px',
            borderRadius: 'var(--r-md) 0 0 var(--r-md)',
            background: t.type === 'success' ? 'var(--ok)' : t.type === 'error' ? 'var(--err)' : 'var(--warn)'
          }} />
        </div>
      ))}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>,
    document.body
  )
}
