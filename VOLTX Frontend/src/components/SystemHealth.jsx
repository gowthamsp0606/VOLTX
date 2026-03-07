import PulseDot from './PulseDot'

const SERVICES = [
  { label: 'Backend API',   icon: '🗄' },
  { label: 'Solana Devnet', icon: '🔗' },
  { label: 'ESP32 Sensors', icon: '📡' },
  { label: 'AI Model',      icon: '🧠' },
]

export default function SystemHealth({ connected }) {
  const color  = connected ? '#22c55e' : '#ef4444'
  const label  = connected ? 'ONLINE'  : 'OFFLINE'

  return (
    <div className="card">
      <div className="ai-section-title">SYSTEM HEALTH</div>

      {SERVICES.map(s => (
        <div key={s.label} className="health-row">
          <div className="health-label">
            <span className="health-icon">{s.icon}</span>
            {s.label}
          </div>
          <div className="health-status" style={{ color }}>
            <PulseDot color={color} />
            {label}
          </div>
        </div>
      ))}
    </div>
  )
}
