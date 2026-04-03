const API_BASE = 'http://localhost:8000'

export const getToken = () => localStorage.getItem('token')

const headers = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${getToken()}`,
})

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error('Login failed')
  return res.json()
}

export async function meFromToken() {
  const users = await api('/users')
  const token = getToken()
  if (!token) return null
  const payload = JSON.parse(atob(token.split('.')[1]))
  return users.find((u) => u.id === Number(payload.sub))
}

export async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers(), ...(options.headers || {}) },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Request failed')
  }
  return res.json()
}
