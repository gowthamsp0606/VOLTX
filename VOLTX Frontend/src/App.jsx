import { useState, useEffect, useRef, useCallback } from 'react'
import { fetchStatus, fetchHistory } from './services/api'
import Sidebar from './components/Sidebar'
import IPConfigBar from './components/IPConfigBar'
import StatusCards from './components/StatusCards'
import EnergyChart from './components/EnergyChart'
import AIPanel from './components/AIPanel'
import TransactionPanel from './components/TransactionPanel'
import SystemHealth from './components/SystemHealth'
import HistoryTable from './components/HistoryTable'
import TheftAlert from './components/TheftAlert'

import './app.css'

export default function App() {
  const [activeNav, setActiveNav] = useState('dashboard')
  const [ip, setIp] = useState('')
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [apiError, setApiError] = useState('')
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [alerts, setAlerts] = useState([])

  // rolling chart data (keeps last 60 points)
  const [voltSeries, setVoltSeries] = useState([])
  const [currSeries, setCurrSeries] = useState([])

  const intervalRef = useRef(null)
  const alertIdRef = useRef(0)
  const prevTheftRef = useRef(false)

  const poll = useCallback(async (hostIp) => {
    try {
      const [s, h] = await Promise.all([
        fetchStatus(hostIp),
        fetchHistory(hostIp),
      ])

      const hasData = s && s.voltage !== undefined && s.current !== undefined
      if (!hasData) {
        setConnected(true)
        setApiError('⏳ Waiting for ESP32 to POST to /predict ...')
        return
      }

      const enriched = { ...s, theft: s.theft === true, ts: Date.now() }
      setStatus(enriched)
      setHistory(Array.isArray(h) ? h.slice(0, 50) : [])

      setVoltSeries(prev => [...prev.slice(-59), { t: Date.now(), v: s.voltage }])
      setCurrSeries(prev => [...prev.slice(-59), { t: Date.now(), v: s.current }])

      // fire alert only on rising edge of theft
      if (s.theft && !prevTheftRef.current) {
        const id = alertIdRef.current++
        setAlerts(a => [...a, { id, ...enriched }])
        setTimeout(() => setAlerts(a => a.filter(x => x.id !== id)), 8000)
      }
      prevTheftRef.current = !!s.theft

      setConnected(true)
      setApiError('')
    } catch (err) {
      setConnected(false)
      setApiError(err.message.includes('fetch') ? 'Cannot reach host' : err.message)
    }
  }, [])

  const handleConnect = useCallback(async (hostIp) => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    setIp(hostIp)
    setConnecting(true)
    setApiError('')
    await poll(hostIp)
    setConnecting(false)
    intervalRef.current = setInterval(() => poll(hostIp), 2000)
  }, [poll])

  const handleDisconnect = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    setConnected(false)
    setStatus(null)
    setHistory([])
    setVoltSeries([])
    setCurrSeries([])
    setApiError('')
    prevTheftRef.current = false
  }, [])

  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current) }, [])

  return (
    <div className="app-shell">
      {/* Theft alert toasts */}
      <div className="alert-stack">
        {alerts.map(a => (
          <TheftAlert key={a.id} event={a} onDismiss={() => setAlerts(p => p.filter(x => x.id !== a.id))} />
        ))}
      </div>

      <Sidebar active={activeNav} onNav={setActiveNav} connected={connected} ip={ip} />

      <main className="main-content">
        {/* Hero */}
        <header className="hero">
          <span className="hero-tag">◆ VOLTX NEURAL NET v2.4 · DEVNET</span>
          <h1 className="hero-title">VOLT<span className="hero-x">X</span></h1>
          <p className="hero-sub">AI + BLOCKCHAIN POWERED ENERGY THEFT DETECTION</p>
          <div className="hero-badges">
            {['ESP32 SENSORS', 'FastAPI', 'AI MODEL', 'SOLANA DEVNET'].map((b, i) => (
              <span key={b} className="badge">{i > 0 && <span className="badge-arrow">→</span>}{b}</span>
            ))}
          </div>
        </header>

        {/* IP input bar — always visible */}
        <IPConfigBar
          ip={ip}
          connected={connected}
          connecting={connecting}
          error={apiError}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
        />

        {/* Empty / waiting state */}
        {!status && (
          <div className="empty-state">
            <div className="empty-icon">⚡</div>
            {connected ? (
              <>
                <p className="empty-title connected">● BACKEND REACHABLE</p>
                <p className="empty-sub">Waiting for ESP32 to POST to <code>/predict</code> ...</p>
                <p className="empty-hint">Dashboard populates automatically on first sensor reading</p>
              </>
            ) : (
              <>
                <p className="empty-title">ENTER YOUR FASTAPI IP ABOVE</p>
                <p className="empty-sub">Connects to <code>http://&#123;ip&#125;:8000/status</code> and <code>/history</code></p>
                <p className="empty-hint">Polls every 2 seconds · Data flows when ESP32 sends readings</p>
              </>
            )}
          </div>
        )}

        {/* ── TAB CONTENT ── */}
        {status && activeNav === 'dashboard' && (
          <>
            <StatusCards status={status} />
            <div className="row-2"><EnergyChart voltSeries={voltSeries} currSeries={currSeries} /></div>
            <div className="row-3">
              <AIPanel status={status} />
              <TransactionPanel status={status} />
              <SystemHealth connected={connected} />
            </div>
            <HistoryTable history={history} />
          </>
        )}

        {status && activeNav === 'analytics' && (
          <div className="tab-page">
            <div className="tab-page-title">📈 ANALYTICS</div>
            <div className="row-2"><EnergyChart voltSeries={voltSeries} currSeries={currSeries} /></div>
            <div className="analytics-stats">
              {[
                { label: 'AVG VOLTAGE', value: voltSeries.length ? (voltSeries.reduce((a,b)=>a+b.v,0)/voltSeries.length).toFixed(1)+'V' : '—', color: '#3b82f6' },
                { label: 'AVG CURRENT', value: currSeries.length ? (currSeries.reduce((a,b)=>a+b.v,0)/currSeries.length).toFixed(2)+'A' : '—', color: '#06b6d4' },
                { label: 'THEFT EVENTS', value: history.filter(h=>h.theft).length, color: '#ef4444' },
                { label: 'TOTAL READINGS', value: history.length, color: '#22c55e' },
                { label: 'PEAK VOLTAGE',  value: voltSeries.length ? Math.max(...voltSeries.map(d=>d.v)).toFixed(1)+'V' : '—', color: '#a78bfa' },
                { label: 'PEAK CURRENT',  value: currSeries.length ? Math.max(...currSeries.map(d=>d.v)).toFixed(2)+'A' : '—', color: '#f59e0b' },
              ].map(s => (
                <div key={s.label} className="card stat-card" style={{ borderColor: s.color+'33' }}>
                  <div className="stat-label">{s.label}</div>
                  <div className="stat-value" style={{ color: s.color, fontSize: 28 }}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {status && activeNav === 'blockchain' && (
          <div className="tab-page">
            <div className="tab-page-title">🔗 BLOCKCHAIN TRANSACTIONS</div>
            <div className="row-3" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <TransactionPanel status={status} />
              <div className="card">
                <div className="ai-section-title">SOLANA NETWORK</div>
                {[
                  { label: 'Network',   value: 'Devnet',                    color: '#a78bfa' },
                  { label: 'Program ID',value: '8xjuMhJ...N5rB',           color: '#94a3b8' },
                  { label: 'TX Count',  value: history.filter(h=>h.tx).length, color: '#22c55e' },
                  { label: 'Status',    value: connected ? 'Connected' : 'Offline', color: connected ? '#22c55e' : '#ef4444' },
                ].map(r => (
                  <div key={r.label} className="health-row">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)' }}>{r.label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: r.color }}>{r.value}</span>
                  </div>
                ))}
              </div>
            </div>
            <HistoryTable history={history.filter(h => h.tx)} />
          </div>
        )}

        {activeNav === 'devices' && (
          <div className="tab-page">
            <div className="tab-page-title">📡 DEVICES</div>
            <div className="row-3">
              {[
                { name: 'ESP32 Sensor #1', role: 'Voltage + Current', status: connected ? 'ONLINE' : 'OFFLINE', color: connected ? '#22c55e' : '#ef4444', icon: '📡' },
                { name: 'FastAPI Server',  role: 'AI Inference',       status: connected ? 'ONLINE' : 'OFFLINE', color: connected ? '#22c55e' : '#ef4444', icon: '🖥' },
                { name: 'Solana Node',     role: 'Blockchain RPC',     status: connected ? 'ONLINE' : 'OFFLINE', color: connected ? '#22c55e' : '#ef4444', icon: '🔗' },
              ].map(d => (
                <div key={d.name} className={`card ${connected ? 'glow-green' : 'glow-red'}`}>
                  <div style={{ fontSize: 32, marginBottom: 12 }}>{d.icon}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text)', marginBottom: 4 }}>{d.name}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', marginBottom: 14 }}>{d.role}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, boxShadow: `0 0 8px ${d.color}` }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: d.color }}>{d.status}</span>
                  </div>
                  {status && d.name.includes('ESP32') && (
                    <div style={{ marginTop: 12, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--dim)', lineHeight: 1.8 }}>
                      Last V: <span style={{ color: '#3b82f6' }}>{status.voltage}V</span><br />
                      Last A: <span style={{ color: '#06b6d4' }}>{status.current}A</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <SystemHealth connected={connected} />
          </div>
        )}

        {activeNav === 'settings' && (
          <div className="tab-page">
            <div className="tab-page-title">⚙ SETTINGS</div>
            <div className="card" style={{ maxWidth: 560 }}>
              <div className="ai-section-title">CONNECTION</div>
              <IPConfigBar
                ip={ip}
                connected={connected}
                connecting={connecting}
                error={apiError}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
              />
              <div className="ai-section-title" style={{ marginTop: 20 }}>ABOUT</div>
              {[
                { label: 'App Name',    value: 'VOLTX' },
                { label: 'Version',     value: 'v2.4.1' },
                { label: 'Network',     value: 'Solana Devnet' },
                { label: 'Poll Rate',   value: 'Every 2 seconds' },
                { label: 'Model',       value: 'theft_model.pkl (SVM)' },
              ].map(r => (
                <div key={r.label} className="health-row">
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)' }}>{r.label}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text)' }}>{r.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
