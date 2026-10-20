import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Alert from '../components/Alert'

export default function Register() {
  const [form, setForm] = useState({
    email: '', password: '', role: 'customer',
    phone: '', address: '', customer_age: '', company_name: '', business_type: '', department: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const payload = {
        email: form.email,
        password: form.password,
        role: form.role,
      }
      if (form.role === 'customer') {
        payload.phone = form.phone
        payload.address = form.address
        payload.customer_age = Number(form.customer_age) || null
      } else if (form.role === 'merchant') {
        payload.company_name = form.company_name
        payload.business_type = form.business_type
      } else if (form.role === 'admin') {
        payload.department = form.department
      }
      const u = await register(payload)
      if (u.role === 'admin') navigate('/admin')
      else if (u.role === 'merchant') navigate('/merchant')
      else navigate('/customer')
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h2>Register</h2>
        <Alert type="danger" message={error} />
        <label>Role</label>
        <select value={form.role} onChange={set('role')}>
          <option value="customer">Customer</option>
          <option value="merchant">Merchant</option>
          <option value="admin">Admin</option>
        </select>
        <label>Email</label>
        <input type="email" value={form.email} onChange={set('email')} required />
        <label>Password (min 6 chars)</label>
        <input type="password" value={form.password} onChange={set('password')} required />

        {form.role === 'customer' && (
          <>
            <label>Phone</label>
            <input value={form.phone} onChange={set('phone')} />
            <label>Address</label>
            <input value={form.address} onChange={set('address')} />
            <label>Age</label>
            <input type="number" value={form.customer_age} onChange={set('customer_age')} />
          </>
        )}
        {form.role === 'merchant' && (
          <>
            <label>Company Name</label>
            <input value={form.company_name} onChange={set('company_name')} required />
            <label>Business Type</label>
            <input value={form.business_type} onChange={set('business_type')} />
          </>
        )}
        {form.role === 'admin' && (
          <>
            <label>Department</label>
            <input value={form.department} onChange={set('department')} />
          </>
        )}

        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? 'Creating...' : 'Register'}
        </button>
        <p className="auth-switch">
          Already have an account? <a href="/login">Login</a>
        </p>
      </form>
    </div>
  )
}
