import { useState, useEffect, useRef, useCallback } from 'react'
import Header from './components/Header'
import PCGrid from './components/PCGrid'
import Sidebar from './components/Sidebar'
import PCModal from './components/PCModal'
import RegisterModal from './components/RegisterModal'
import ScanModal from './components/ScanModal'
import { ToastContainer, toast } from './components/Toast'
import './App.css'

const API = '/api'
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_URL = `${wsProtocol}//${window.location.host}/ws`

function formatDowntime(secs) {
  if (!secs) return null
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

export default function App() {
  const [pcs, setPcs] = useState([])
  const [events, setEvents] = useState([])
  const [selectedPC, setSelectedPC] = useState(null)
  const [showRegister, setShowRegister] = useState(false)
  const [showScan, setShowScan] = useState(false)
  const [wsStatus, setWsStatus] = useState('connecting')
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('codere-theme') === 'dark'
  })
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  // Apply dark mode class to root
  useEffect(() => {
    const root = document.documentElement
    if (darkMode) {
      root.classList.add('dark')
      localStorage.setItem('codere-theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('codere-theme', 'light')
    }
  }, [darkMode])

  const handleMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'initial_state':
        setPcs(msg.data.pcs)
        setEvents(msg.data.events || [])
        break

      case 'metrics_update':
        setPcs(prev => prev.map(pc =>
          pc.id === msg.data.pc_id
            ? { ...pc, status: msg.data.status, last_seen: msg.data.last_seen, last_metrics: msg.data.metrics }
            : pc
        ))
        setSelectedPC(prev =>
          prev?.id === msg.data.pc_id
            ? { ...prev, status: msg.data.status, last_metrics: msg.data.metrics, last_seen: msg.data.last_seen }
            : prev
        )
        break

      case 'status_change':
        setPcs(prev => prev.map(pc =>
          pc.id === msg.data.pc_id ? { ...pc, status: msg.data.status } : pc
        ))
        break

      case 'event': {
        const ev = msg.data
        setEvents(prev => [ev, ...prev].slice(0, 100))
        if (ev.event_type === 'offline') {
          toast.error(`La máquina ${ev.pc_name} se ha desconectado.`)
          setPcs(prev => prev.map(pc =>
            pc.id === ev.pc_id ? { ...pc, status: 'offline' } : pc
          ))
        } else if (ev.event_type === 'online') {
          const dt = formatDowntime(ev.downtime_seconds)
          toast.success(`${ev.pc_name} vuelve a estar en línea${dt ? ` (Downtime: ${dt})` : ''}.`)
          setPcs(prev => prev.map(pc =>
            pc.id === ev.pc_id ? { ...pc, status: 'online' } : pc
          ))
        }
        break
      }

      case 'pc_registered':
        setPcs(prev => {
          if (prev.find(p => p.id === msg.data.id)) return prev
          return [...prev, msg.data]
        })
        break

      case 'pc_deleted':
        setPcs(prev => prev.filter(p => p.id !== msg.data.pc_id))
        setSelectedPC(prev => prev?.id === msg.data.pc_id ? null : prev)
        break

      default:
        break
    }
  }, [])

  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return

    setWsStatus('connecting')
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setWsStatus('open')
      if (reconnectTimer.current) {
        clearInterval(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (e) => {
      try {
        handleMessage(JSON.parse(e.data))
      } catch {}
    }

    ws.onclose = () => {
      setWsStatus('closed')
      if (!reconnectTimer.current) {
        reconnectTimer.current = setInterval(connectWS, 3000)
      }
    }

    ws.onerror = () => ws.close()
  }, [handleMessage])

  useEffect(() => {
    connectWS()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null // Evitar loop de reconexión al desmontar
        wsRef.current.close()
      }
      if (reconnectTimer.current) {
        clearInterval(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }
  }, [connectWS])

  // Keep-alive ping every 30s
  useEffect(() => {
    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000)
    return () => clearInterval(ping)
  }, [])

  const handleRegister = async (ip, name) => {
    const resp = await fetch(`${API}/pcs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, name }),
    })
    const data = await resp.json()
    if (!resp.ok) throw new Error(data.detail || 'Error al registrar')
    setPcs(prev => {
      if (prev.find(p => p.id === data.id)) return prev
      return [...prev, data]
    })
    toast.success(`La máquina ${name} fue registrada exitosamente.`)
  }

  const handleDelete = async (pcId) => {
    await fetch(`${API}/pcs/${pcId}`, { method: 'DELETE' })
    setPcs(prev => prev.filter(p => p.id !== pcId))
    setSelectedPC(null)
    toast.warning('La máquina fue eliminada del inventario.')
  }

  const stats = {
    total: pcs.length,
    online: pcs.filter(p => p.status === 'online').length,
    offline: pcs.filter(p => p.status === 'offline').length,
    unknown: pcs.filter(p => p.status === 'unknown').length,
  }

  return (
    <div className="app">
      <Header
        stats={stats}
        wsStatus={wsStatus}
        onRegister={() => setShowRegister(true)}
        onScan={() => setShowScan(true)}
        apiUrl={API}
        darkMode={darkMode}
        onToggleDark={() => setDarkMode(d => !d)}
      />

      <div className="main-layout">
        <div className="content-area">
          <PCGrid
            pcs={pcs}
            onSelect={setSelectedPC}
            selectedId={selectedPC?.id}
          />
        </div>
        <Sidebar events={events} />
      </div>

      {selectedPC && (
        <PCModal
          pc={selectedPC}
          onClose={() => setSelectedPC(null)}
          onDelete={handleDelete}
          apiUrl={API}
        />
      )}

      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onRegister={handleRegister}
        />
      )}

      {showScan && (
        <ScanModal
          onClose={() => setShowScan(false)}
          onRegister={handleRegister}
          apiUrl={API}
          existingIPs={pcs.map(p => p.ip)}
        />
      )}

      <ToastContainer />
    </div>
  )
}
