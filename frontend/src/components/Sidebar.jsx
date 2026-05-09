function Sidebar({ page, onChange }) {
  const items = [
    { id: 'chat',      label: 'Chat' },
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'history',   label: 'History' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>Insights AI</h1>
        <p>Entertainment Analytics</p>
      </div>
      <nav className="sidebar-nav">
        {items.map(item => (
          <button
            key={item.id}
            className={`nav-btn ${page === item.id ? 'active' : ''}`}
            onClick={() => onChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer muted">
        Powered by Groq · Llama 3.3
      </div>
    </aside>
  )
}

export default Sidebar
