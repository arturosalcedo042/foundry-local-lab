import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Database, GitBranch, Layers, RefreshCw } from 'lucide-react'
import './style.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
function App() {
  const [summary, setSummary] = useState(null)
  const [orders, setOrders] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function refresh() {
    try {
      const [a,b] = await Promise.all([fetch(`${API}/summary`),fetch(`${API}/orders`)])
      if (!a.ok || !b.ok) throw Error('API request failed')
      setSummary(await a.json()); setOrders(await b.json()); setError('')
    } catch (e) { setError(`${e.message}. Confirm Docker containers are running.`) }
  }
  useEffect(() => { refresh() }, [])
  async function changeStatus(order, status) {
    setBusy(true)
    try {
      const r = await fetch(`${API}/orders/${order}/status`, { method:'PATCH', headers:{'Content-Type':'application/json'},body:JSON.stringify({status}) })
      if (!r.ok) throw Error(await r.text())
      await refresh()
    } catch(e) { setError(e.message) } finally { setBusy(false) }
  }
  return <main>
    <header><div><p className="eyebrow">LOCAL DATA OPERATIONS</p><h1>Foundry-inspired Lab</h1><p>Datasets → PySpark transforms → PostgreSQL objects → React operational actions</p></div><button onClick={refresh}><RefreshCw size={16}/> Refresh</button></header>
    <section className="pipeline"><div><Database/> Raw CSV datasets</div><span>→</span><div><GitBranch/> Spark ETL</div><span>→</span><div><Layers/> Ontology-like tables</div><span>→</span><div>Operational UI</div></section>
    {error && <p className="error">{error}</p>}
    {!summary?.pipeline && <p className="hint">No pipeline run yet. In PowerShell run: <code>docker compose run --rm etl</code></p>}
    <section className="metrics"><article><small>Orders</small><strong>{summary?.orders ?? '—'}</strong></article><article><small>Total order value</small><strong>${(summary?.revenue ?? 0).toLocaleString(undefined,{maximumFractionDigits:2})}</strong></article><article><small>Pending orders</small><strong>{summary?.pending ?? '—'}</strong></article><article><small>Last pipeline run</small><strong className="small">{summary?.pipeline ? new Date(summary.pipeline.ran_at).toLocaleString() : 'Not run'}</strong></article></section>
    <section className="table-card"><div className="card-title"><h2>Order objects</h2><span>{orders.length} records</span></div><div className="table-scroll"><table><thead><tr><th>Order</th><th>Customer</th><th>Region</th><th>Amount</th><th>Payment</th><th>Status action</th></tr></thead><tbody>{orders.map(o=><tr key={o.order_id}><td>#{o.order_id}</td><td>{o.customer_name}</td><td>{o.region}</td><td>${o.amount.toFixed(2)}</td><td><span className={'tag '+o.payment_status}>{o.payment_status}</span></td><td><select aria-label={'Order '+o.order_id+' status'} disabled={busy} value={o.status} onChange={e=>changeStatus(o.order_id,e.target.value)}>{['pending','shipped','delivered','cancelled'].map(v=><option key={v}>{v}</option>)}</select></td></tr>)}</tbody></table></div></section>
    <footer>Educational Foundry simulation — no affiliation with Palantir. Not production hardened.</footer>
  </main>
}

createRoot(document.getElementById('root')).render(<App />)
