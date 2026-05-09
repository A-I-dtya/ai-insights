import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const API_URL = 'http://localhost:8000/chat'

const SUGGESTIONS = [
  'Top movies of 2025',
  'Why is Stellar Run trending?',
  'Compare Dark Orbit vs Last Kingdom',
  'Best engagement city last month',
  'What explains weak comedy performance?',
  'What does the executive report recommend?',
]

function Chat({ onLog }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm your AI Insights Assistant. Ask about movies, audience, regions, or strategy.",
      tool_calls: [],
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || loading) return

    setMessages(m => [...m, { role: 'user', content: msg }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      })
      const data = await res.json()
      const reply = {
        role: 'assistant',
        content: data.answer ?? '(empty response)',
        tool_calls: data.tool_calls ?? [],
      }
      setMessages(m => [...m, reply])
      onLog?.({ question: msg, answer: reply.content, tools: reply.tool_calls })
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', content: `Error: ${err.message}`, tool_calls: [] }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h2>AI Assistant</h2>
        <p className="muted">Ask anything — answers are grounded in your database and PDF reports.</p>
      </header>

      <main className="messages">
        {messages.map((m, i) => (
          <Message key={i} {...m} />
        ))}
        {loading && (
          <div className="message assistant">
            <div className="avatar">AI</div>
            <div className="bubble">
              <span className="dots"><span /><span /><span /></span>
              <span className="muted">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <footer className="footer">
        {messages.length <= 1 && (
          <div className="suggestions">
            {SUGGESTIONS.map(s => (
              <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}
        <div className="input-row">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a question…  (Enter to send, Shift+Enter for newline)"
            rows={1}
            disabled={loading}
          />
          <button onClick={() => send()} disabled={!input.trim() || loading}>
            Send
          </button>
        </div>
      </footer>
    </div>
  )
}

function Message({ role, content, tool_calls }) {
  const isUser = role === 'user'
  const [open, setOpen] = useState(false)

  return (
    <div className={`message ${role}`}>
      <div className="avatar">{isUser ? 'You' : 'AI'}</div>
      <div className="bubble">
        <ReactMarkdown>{content}</ReactMarkdown>
        {!isUser && tool_calls?.length > 0 && (
          <details className="tools-dropdown" open={open} onToggle={(e) => setOpen(e.target.open)}>
            <summary>
              <span className="muted">
                {open ? '<' : '>'} Tools used ({tool_calls.length})
              </span>
            </summary>
            <div className="tools-list">
              {tool_calls.map((tc, i) => (
                <div key={i} className="tool-row">
                  <span className="tool-chip">{tc.name}</span>
                  <code className="tool-args">{JSON.stringify(tc.args)}</code>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  )
}

export default Chat
