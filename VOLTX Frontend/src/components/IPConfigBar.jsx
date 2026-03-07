import { useState } from 'react'
import PulseDot from './PulseDot'

export default function IPConfigBar({ ip, connected, connecting, error, onConnect, onDisconnect }) {
  const [val, setVal] = useState(ip || '')

  const go = () => { const t = val.trim(); if (t) onConnect(t) }

  const barClass = `ip-bar${connected ? ' connected' : error && !connecting ? ' error-state' : ''}`

  return (
    <div className={barClass}>
      <span style={{ fontSize: 16 }}>🖥</span>
      <span className="ip-label">BACKEND IP</span>

      <div className="ip-input-wrap">
        <span className="ip-prefix">http://</span>
        <input
          className="ip-input"
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && go()}
          placeholder="192.168.1.100"
          disabled={connected}
        />
        <span className="ip-suffix">:8000</span>
      </div>

      {!connected ? (
        <button className="btn-connect" onClick={go} disabled={connecting || !val.trim()}>
          {connecting ? '↻ CONNECTING...' : '▶ CONNECT'}
        </button>
      ) : (
        <button className="btn-disconnect" onClick={onDisconnect}>
          ■ DISCONNECT
        </button>
      )}

      <div className={`ip-status ${connected ? 'live' : error ? 'err' : 'idle'}`}>
        {connected && <><PulseDot color="#22c55e" /> LIVE DATA</>}
        {!connected && error && <span>⚠ {error}</span>}
        {!connected && !error && !connecting && <span>AWAITING HOST</span>}
      </div>
    </div>
  )
}
