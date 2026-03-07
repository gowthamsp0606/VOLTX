const NAV = [
  { id: 'dashboard',  label: 'Dashboard',  icon: '⊞' },
  { id: 'analytics',  label: 'Analytics',  icon: '📈' },
  { id: 'blockchain', label: 'Blockchain', icon: '🔗' },
  { id: 'devices',    label: 'Devices',    icon: '📡' },
  { id: 'settings',   label: 'Settings',   icon: '⚙' },
]

export default function Sidebar({ active, onNav, connected, ip }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">⚡</div>
        <div>
          <div className="logo-name">VOLTX</div>
          <div className="logo-tag">AI SHIELD</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(item => (
          <button
            key={item.id}
            className={`nav-btn ${active === item.id ? 'active' : ''}`}
            onClick={() => onNav(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        {ip
          ? <><span className="host">HOST: </span>{ip}:8000<br /></>
          : <span>NO HOST SET<br /></span>
        }
        <span className={connected ? 'online' : 'offline'}>
          {connected ? '● LIVE' : '● OFFLINE'}
        </span>
      </div>
    </aside>
  )
}
