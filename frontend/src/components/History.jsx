function History({ items, onRemove, onClearAll }) {
  return (
    <div className="page">
      <header className="page-header" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <h2>Query History</h2>
          <p className="muted">Last {items.length} questions asked in this session.</p>
        </div>
        {items.length > 0 && (
          <button className="clear-all-btn" onClick={onClearAll}>
            Clear all
          </button>
        )}
      </header>

      <main className="page-body">
        {items.length === 0 ? (
          <p className="muted">No queries yet. Head to the Chat tab.</p>
        ) : (
          <div className="history-list">
            {items.map((h) => (
              <div key={h.id} className="history-item">
                <button
                  className="history-delete"
                  onClick={() => onRemove(h.id)}
                  title="Delete this entry"
                >
                  ×
                </button>
                <div className="history-q">{h.question}</div>
                <div className="history-a muted">
                  {h.answer.slice(0, 150)}{h.answer.length > 150 ? '…' : ''}
                </div>
                {h.tools?.length > 0 && (
                  <div className="history-tools">
                    {h.tools.map((t, j) => (
                      <span key={j} className="tool-chip">{t.name}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default History
