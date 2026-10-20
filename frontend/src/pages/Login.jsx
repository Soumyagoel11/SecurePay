import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Alert from '../components/Alert'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const u = await login(email, password)
      if (u.role === 'admin') navigate('/admin')
      else if (u.role === 'merchant') navigate('/merchant')
      else navigate('/customer')
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h2>Login</h2>
        <Alert type="danger" message={error} />
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label>Password</label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          required
        />
        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? 'Logging in...' : 'Login'}
        </button>
        <p className="auth-switch">
          No account? <a href="/register">Register</a>
        </p>
      </form>
    </div>
  )
}
