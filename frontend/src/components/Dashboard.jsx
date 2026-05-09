import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'

const API = 'http://localhost:8000/api/analytics'
const COLORS = ['#58a6ff', '#3fb950', '#bc8cff', '#f0883e', '#f85149', '#79c0ff', '#56d364']

const fmtMoney = (n) => {
  if (n == null) return '—'
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  return `$${n.toLocaleString()}`
}
const fmtNum = (n) => {
  if (n == null) return '—'
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`
  return n.toLocaleString()
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1c2128', border: '1px solid #30363d',
      padding: '8px 12px', borderRadius: 6, fontSize: 12,
    }}>
      <div style={{ color: '#8b949e', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#58a6ff' }}>
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  )
}

function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [genres,   setGenres]   = useState([])
  const [regional, setRegional] = useState([])
  const [trending, setTrending] = useState([])
  const [audience, setAudience] = useState([])
  const [audSeg,   setAudSeg]   = useState('age')
  const [year,     setYear]     = useState('')
  const [loading,  setLoading]  = useState(true)

  // Load everything in parallel
  useEffect(() => {
    setLoading(true)
    const yp = year ? `?year=${year}` : ''
    const yearParam = year ? `&year=${year}` : ''
    Promise.all([
      fetch(`${API}/overview${yp}`).then(r => r.json()),
      fetch(`${API}/genres${yp}`).then(r => r.json()),
      fetch(`${API}/regional?limit=10${yearParam}`).then(r => r.json()),
      fetch(`${API}/trending?days=30&limit=5`).then(r => r.json()),
      fetch(`${API}/audience?segment=${audSeg}`).then(r => r.json()),
    ]).then(([ov, gn, rg, tr, au]) => {
      setOverview(ov)
      setGenres((gn.genres || []).map(g => ({
        ...g,
        revenue_m: +(g.total_revenue / 1e6).toFixed(1),
      })))
      setRegional(rg.regions || [])
      setTrending(tr.trending || [])
      setAudience(au.data || [])
    }).catch(console.error).finally(() => setLoading(false))
  }, [year, audSeg])

  // Auto-generated insights
  const insights = buildInsights({ overview, genres, regional, trending })

  if (loading) {
    return (
      <div className="page">
        <header className="page-header"><h2>Analytics Dashboard</h2></header>
        <main className="page-body"><p className="muted">Loading…</p></main>
      </div>
    )
  }

  return (
    <div className="page">
      <header className="page-header" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <h2>Analytics Dashboard</h2>
          <p className="muted">Overview of platform performance across all data sources.</p>
        </div>
        <div className="filter-row">
          <label className="muted">Year:</label>
          <select value={year} onChange={e => setYear(e.target.value)}>
            <option value="">All years</option>
            <option value="2023">2023</option>
            <option value="2024">2024</option>
            <option value="2025">2025</option>
          </select>
        </div>
      </header>

      <main className="page-body">
        {/* KPI Cards */}
        <div className="kpi-grid">
          <KpiCard label="Movies"    value={overview?.total_movies} />
          <KpiCard label="Viewers"   value={fmtNum(overview?.total_viewers)} />
          <KpiCard label="Views"     value={fmtNum(overview?.total_views)} />
          <KpiCard label="Revenue"   value={`$${overview?.total_revenue_m ?? '—'}M`} />
          <KpiCard label="Avg Rating" value={`${overview?.avg_rating ?? '—'}/10`} />
        </div>

        {/* Insights panel */}
        <div className="card">
          <div className="card-title">Key Insights</div>
          <ul className="insights-list">
            {insights.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>

        {/* Charts grid */}
        <div className="charts-grid">
          {/* Genre revenue */}
          <div className="card">
            <div className="card-title">Revenue by Genre ($M)</div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={genres} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="genre" tick={{ fill: '#8b949e', fontSize: 11 }} angle={-25} textAnchor="end" />
                <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="revenue_m" name="Revenue ($M)" radius={[4, 4, 0, 0]}>
                  {genres.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top cities */}
          <div className="card">
            <div className="card-title">Top Cities by Engagement</div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={regional} layout="vertical" margin={{ top: 8, right: 16, left: 60, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis type="number" domain={[0, 10]} tick={{ fill: '#8b949e', fontSize: 11 }} />
                <YAxis type="category" dataKey="city" tick={{ fill: '#8b949e', fontSize: 11 }} width={70} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="avg_engagement" name="Engagement" radius={[0, 4, 4, 0]}>
                  {regional.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trending */}
          <div className="card">
            <div className="card-title">Trending — Recent 30 Days</div>
            <ul className="trending-list">
              {trending.length === 0 && <li className="muted">No trending data</li>}
              {trending.map((t, i) => (
                <li key={i}>
                  <span className="trending-rank">#{i + 1}</span>
                  <span className="trending-title">{t.title}</span>
                  <span className="muted trending-genre">{t.genre}</span>
                  <span className="trending-views">{t.recent_views} views</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Audience */}
          <div className="card">
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>Audience Segment</span>
              <select
                value={audSeg}
                onChange={e => setAudSeg(e.target.value)}
                className="inline-select"
              >
                <option value="age">Age</option>
                <option value="subscription">Subscription</option>
                <option value="device">Device</option>
                <option value="genre_preference">Genre Preference</option>
              </select>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={audience}
                  dataKey="viewers"
                  nameKey={audKey(audSeg)}
                  cx="50%" cy="50%"
                  outerRadius={80}
                  label={(e) => e[audKey(audSeg)]}
                >
                  {audience.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#8b949e' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </main>
    </div>
  )
}

function audKey(seg) {
  return {
    age: 'age_group',
    subscription: 'subscription_tier',
    device: 'device',
    genre_preference: 'preferred_genre',
  }[seg] || 'age_group'
}

function KpiCard({ label, value }) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value ?? '—'}</div>
    </div>
  )
}

function buildInsights({ overview, genres, regional, trending }) {
  const out = []
  if (genres.length) {
    const top = genres[0]
    out.push(`Top revenue genre: ${top.genre} (${fmtMoney(top.total_revenue)}, ROI ${top.roi}x)`)
    const worst = [...genres].sort((a, b) => (a.roi || 0) - (b.roi || 0))[0]
    if (worst) out.push(`Lowest ROI genre: ${worst.genre} at ${worst.roi}x`)
    const ratings = [...genres].sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0))
    if (ratings[0]) out.push(`Highest-rated genre: ${ratings[0].genre} (${ratings[0].avg_rating}/10)`)
  }
  if (regional.length) {
    out.push(`Top engagement city: ${regional[0].city} (${regional[0].avg_engagement}/10)`)
  }
  if (trending.length) {
    out.push(`Most-watched recent title: ${trending[0].title} (${trending[0].recent_views} views)`)
  }
  if (overview?.total_revenue_m) {
    out.push(`Platform total revenue: $${overview.total_revenue_m}M across ${overview.total_movies} titles`)
  }
  return out
}

export default Dashboard
