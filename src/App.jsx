import { useEffect, useMemo, useState } from 'react'
import { api, getToken, login, meFromToken } from './api'
import './App.css'

function App() {
  const [form, setForm] = useState({ email: 'admin@mandi.local', password: 'admin123' })
  const [user, setUser] = useState(null)
  const [error, setError] = useState('')
  const [stock, setStock] = useState([])
  const [sales, setSales] = useState([])
  const [users, setUsers] = useState([])
  const [adminMetrics, setAdminMetrics] = useState(null)

  const [stockForm, setStockForm] = useState({ item_name: '', quantity: 0, price_per_unit: 0 })
  const [userForm, setUserForm] = useState({ name: '', email: '', password: '', role: 'buyer' })
  const [saleForm, setSaleForm] = useState({ buyer_id: '', stock_id: '', quantity: 1 })

  const buyers = useMemo(() => users.filter((u) => u.role === 'buyer'), [users])

  const loadData = async () => {
    if (!getToken()) return
    const [currentUser, stockData, salesData] = await Promise.all([
      meFromToken(),
      api('/stock'),
      api('/sales'),
    ])
    setUser(currentUser)
    setStock(stockData)
    setSales(salesData)

    if (currentUser?.role === 'admin') {
      const [allUsers, dashboard] = await Promise.all([api('/users'), api('/dashboard/admin')])
      setUsers(allUsers)
      setAdminMetrics(dashboard)
    }

    if (currentUser?.role === 'clerk') {
      const allUsers = await api('/users').catch(() => [])
      setUsers(allUsers)
    }
  }

  useEffect(() => {
    loadData().catch((e) => setError(e.message))
  }, [])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const tokenResponse = await login(form.email, form.password)
      localStorage.setItem('token', tokenResponse.access_token)
      await loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const addStock = async (e) => {
    e.preventDefault()
    await api('/stock', { method: 'POST', body: JSON.stringify({ ...stockForm, quantity: Number(stockForm.quantity), price_per_unit: Number(stockForm.price_per_unit) }) })
    setStockForm({ item_name: '', quantity: 0, price_per_unit: 0 })
    await loadData()
  }

  const addUser = async (e) => {
    e.preventDefault()
    await api('/users', { method: 'POST', body: JSON.stringify(userForm) })
    setUserForm({ name: '', email: '', password: '', role: 'buyer' })
    await loadData()
  }

  const createSale = async (e) => {
    e.preventDefault()
    await api('/sales', {
      method: 'POST',
      body: JSON.stringify({
        buyer_id: Number(saleForm.buyer_id),
        items: [{ stock_id: Number(saleForm.stock_id), quantity: Number(saleForm.quantity) }],
      }),
    })
    await loadData()
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  if (!user) {
    return (
      <div className="container py-5">
        <h2 className="mb-4">Mandi Broker Management System</h2>
        <form className="card p-4" onSubmit={handleLogin}>
          <input className="form-control mb-2" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="form-control mb-2" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <button className="btn btn-primary">Login</button>
          <small className="mt-3 text-muted">Default admin: admin@mandi.local / admin123</small>
        </form>
        {error && <div className="alert alert-danger mt-3">{error}</div>}
      </div>
    )
  }

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>{user.role.toUpperCase()} Dashboard</h3>
        <button className="btn btn-outline-danger" onClick={logout}>Logout</button>
      </div>

      <div className="card p-3 mb-3">
        <h5>Available Stock</h5>
        <table className="table table-sm">
          <thead><tr><th>Item</th><th>Qty</th><th>Price</th></tr></thead>
          <tbody>{stock.map((s) => <tr key={s.id}><td>{s.item_name}</td><td>{s.quantity}</td><td>{s.price_per_unit}</td></tr>)}</tbody>
        </table>
      </div>

      {(user.role === 'clerk' || user.role === 'admin') && (
        <div className="row g-3">
          <div className="col-md-6">
            <form className="card p-3" onSubmit={addStock}>
              <h5>Add Stock</h5>
              <input className="form-control mb-2" placeholder="Item" value={stockForm.item_name} onChange={(e) => setStockForm({ ...stockForm, item_name: e.target.value })} />
              <input className="form-control mb-2" type="number" placeholder="Quantity" value={stockForm.quantity} onChange={(e) => setStockForm({ ...stockForm, quantity: e.target.value })} />
              <input className="form-control mb-2" type="number" step="0.1" placeholder="Price per unit" value={stockForm.price_per_unit} onChange={(e) => setStockForm({ ...stockForm, price_per_unit: e.target.value })} />
              <button className="btn btn-success">Save Stock</button>
            </form>
          </div>
          <div className="col-md-6">
            <form className="card p-3" onSubmit={createSale}>
              <h5>Create Sale</h5>
              <select className="form-select mb-2" value={saleForm.buyer_id} onChange={(e) => setSaleForm({ ...saleForm, buyer_id: e.target.value })}>
                <option value="">Select Buyer</option>
                {buyers.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
              <select className="form-select mb-2" value={saleForm.stock_id} onChange={(e) => setSaleForm({ ...saleForm, stock_id: e.target.value })}>
                <option value="">Select Stock</option>
                {stock.map((s) => <option key={s.id} value={s.id}>{s.item_name}</option>)}
              </select>
              <input className="form-control mb-2" type="number" min="1" value={saleForm.quantity} onChange={(e) => setSaleForm({ ...saleForm, quantity: e.target.value })} />
              <button className="btn btn-warning">Sell</button>
            </form>
          </div>
        </div>
      )}

      {user.role === 'admin' && (
        <div className="row g-3 mt-1">
          <div className="col-md-6">
            <form className="card p-3" onSubmit={addUser}>
              <h5>Create User</h5>
              <input className="form-control mb-2" placeholder="Name" value={userForm.name} onChange={(e) => setUserForm({ ...userForm, name: e.target.value })} />
              <input className="form-control mb-2" placeholder="Email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} />
              <input className="form-control mb-2" type="password" placeholder="Password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} />
              <select className="form-select mb-2" value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
                <option value="buyer">Buyer</option>
                <option value="clerk">Clerk</option>
              </select>
              <button className="btn btn-primary">Create User</button>
            </form>
          </div>
          <div className="col-md-6">
            <div className="card p-3">
              <h5>Admin Metrics</h5>
              <p>Total Sales: {adminMetrics?.total_sales ?? 0}</p>
              <p>Total Stock Units: {adminMetrics?.total_stock ?? 0}</p>
              <p>Total Revenue: ₹{adminMetrics?.revenue ?? 0}</p>
            </div>
          </div>
        </div>
      )}

      <div className="card p-3 mt-3">
        <h5>{user.role === 'buyer' ? 'My Purchase History' : 'Sales Transactions'}</h5>
        <table className="table table-sm">
          <thead><tr><th>ID</th><th>Buyer</th><th>Total</th><th>Date</th></tr></thead>
          <tbody>{sales.map((s) => <tr key={s.id}><td>{s.id}</td><td>{s.buyer_id}</td><td>{s.total_amount}</td><td>{new Date(s.created_at).toLocaleString()}</td></tr>)}</tbody>
        </table>
      </div>
      {error && <div className="alert alert-danger mt-3">{error}</div>}
    </div>
  )
}

export default App
