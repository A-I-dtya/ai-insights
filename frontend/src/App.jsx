import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'
import History from './components/History'
import './App.css'

function App() {
  const [page, setPage] = useState('chat')
  const [history, setHistory] = useState([])

  const logQuery = (entry) =>
    setHistory(h => [{ ...entry, ts: new Date(), id: Date.now() + Math.random() }, ...h].slice(0, 50))

  const removeOne = (id)  => setHistory(h => h.filter(item => item.id !== id))
  const clearAll  = ()    => setHistory([])

  return (
    <div className="shell">
      <Sidebar page={page} onChange={setPage} />
      <div className="page-wrap">
        {page === 'chat'      && <Chat onLog={logQuery} />}
        {page === 'dashboard' && <Dashboard />}
        {page === 'history'   && <History items={history} onRemove={removeOne} onClearAll={clearAll} />}
      </div>
    </div>
  )
}

export default App
