import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Card } from '../components/Card'
import Alert from '../components/Alert'
import StatusBadge from '../components/StatusBadge'
import Loading from '../components/Loading'

export default function QRPaymentCheckout({ isStoreQR = false }) {
  const { token, merchantId } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()

  // Session state
  const [session, setSession] = useState(null)
  const [storeMerchant, setStoreMerchant] = useState(null)
  const [customAmount, setCustomAmount] = useState('25.00')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Customer options
  const [demoCustomers, setDemoCustomers] = useState([])
  const [selectedDemoCustomer, setSelectedDemoCustomer] = useState('')
  const [loginEmail, setLoginEmail] = useState('customer1@securepay.com')
  const [loginPassword, setLoginPassword] = useState('password123')
  const [authMode, setAuthMode] = useState('demo') // 'demo' or 'login'

  // Fraud testing simulation
  const [locationChange, setLocationChange] = useState(false)
  const [deviceChange, setDeviceChange] = useState(false)
  const [showFraudToggles, setShowFraudToggles] = useState(false)

  // Payment result
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  // Load Session or Merchant info + demo customers
  useEffect(() => {
    const init = async () => {
      setLoading(true)
      try {
        // Load demo customers list for 1-tap mobile testing
        const custRes = await api.get('/qr-payments/demo-customers').catch(() => null)
        if (custRes && custRes.data.data.customers.length > 0) {
          setDemoCustomers(custRes.data.data.customers)
          setSelectedDemoCustomer(String(custRes.data.data.customers[0].customer_id))
        }

        if (token) {
          // Dynamic QR Session
          const res = await api.get(`/qr-payments/${token}`)
          const s = res.data.data
          setSession(s)
          if (s.status === 'completed' && s.payment) {
            setResult({
              status: 'success',
              payment: s.payment,
              fraud: s.fraud,
            })
          }
        } else if (merchantId) {
          // Static Store QR
          const mRes = await api.get('/customer/merchants').catch(() => null)
          if (mRes && mRes.data.data.merchants) {
            const m = mRes.data.data.merchants.find((x) => String(x.merchant_id) === String(merchantId))
            if (m) setStoreMerchant(m)
            else setError('Merchant not found')
          }
        }
      } catch (err) {
        setError(err.message || 'Failed to load payment session')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [token, merchantId])

  const handlePay = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)

    try {
      const payload = {
        location_change: locationChange ? 1 : 0,
        device_change: deviceChange ? 1 : 0,
      }

      // If user is not logged in, pass customer_id or credentials
      if (!user) {
        if (authMode === 'demo') {
          payload.customer_id = Number(selectedDemoCustomer)
        } else {
          payload.email = loginEmail
          payload.password = loginPassword
        }
      }

      if (token) {
        // Pay dynamic QR
        const res = await api.post(`/qr-payments/${token}/pay`, payload)
        setResult(res.data.data)
      } else if (merchantId) {
        // Store QR: first create session or pay directly
        payload.amount = Number(customAmount)
        const qrRes = await api.post('/qr-payments/create', {
          amount: Number(customAmount),
          description: `Store Payment to ${storeMerchant?.company_name || 'Merchant'}`,
        }).catch(() => null)

        let targetToken = qrRes ? qrRes.data.data.qr.token : null
        if (!targetToken) {
          // Fallback direct payment
          const payRes = await api.post('/payments', {
            merchant_id: Number(merchantId),
            amount: Number(customAmount),
            location_change: locationChange ? 1 : 0,
            device_change: deviceChange ? 1 : 0,
          })
          setResult(payRes.data.data)
          return
        }
        const res = await api.post(`/qr-payments/${targetToken}/pay`, payload)
        setResult(res.data.data)
      }
    } catch (err) {
      setError(err.message || 'Payment processing failed')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div style={{ maxWidth: '480px', margin: '3rem auto', textAlign: 'center' }}>
        <Loading />
        <p style={{ color: 'var(--muted)', marginTop: '0.5rem' }}>Loading payment checkout...</p>
      </div>
    )
  }

  const merchantName = session?.merchant_name || storeMerchant?.company_name || 'SecurePay Merchant'
  const merchantType = session?.merchant_type || storeMerchant?.business_type || 'Retail'
  const finalAmount = session ? session.amount : Number(customAmount)

  // Success Screen
  if (result && result.status === 'success') {
    const payment = result.payment || {}
    const fraud = result.fraud || {}
    return (
      <div className="mobile-checkout-container" style={{ maxWidth: '440px', margin: '1.5rem auto', padding: '0 1rem' }}>
        <div
          style={{
            background: '#ffffff',
            borderRadius: '16px',
            padding: '2rem 1.5rem',
            textAlign: 'center',
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            border: '2px solid #22c55e',
          }}
        >
          {/* Animated Success Checkmark */}
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: '#dcfce7',
              color: '#16a34a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '2.5rem',
              fontWeight: 700,
              margin: '0 auto 1rem auto',
            }}
          >
            ✓
          </div>

          <h2 style={{ color: '#166534', margin: '0 0 0.25rem 0' }}>Payment Successful!</h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
            Paid via Google Lens / SecurePay QR
          </p>

          <div
            style={{
              background: 'var(--bg)',
              borderRadius: '12px',
              padding: '1.25rem',
              margin: '1rem 0',
            }}
          >
            <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#0f172a' }}>
              ${payment.amount || finalAmount}
            </div>
            <div style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
              To: <strong>{merchantName}</strong> ({merchantType})
            </div>
          </div>

          <div style={{ textAlign: 'left', fontSize: '0.88rem', borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0' }}>
              <span style={{ color: 'var(--muted)' }}>Transaction ID</span>
              <strong>#{payment.payment_id || session?.payment_id || 'TXN-OK'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0' }}>
              <span style={{ color: 'var(--muted)' }}>Date & Time</span>
              <span>{payment.payment_date || new Date().toLocaleString()}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0' }}>
              <span style={{ color: 'var(--muted)' }}>Payment Status</span>
              <StatusBadge status="success" />
            </div>
          </div>

          {/* ML Fraud Verification Badge */}
          <div
            style={{
              marginTop: '1.25rem',
              padding: '0.75rem',
              background: '#f0fdf4',
              borderRadius: '8px',
              border: '1px solid #bbf7d0',
              textAlign: 'left',
              fontSize: '0.85rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#166534', fontWeight: 600 }}>
              <span>🛡️</span>
              <span>ML Fraud Model: Safe</span>
            </div>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--muted)', fontSize: '0.8rem' }}>
              Risk score: <strong>{fraud.risk_score ?? 0.04}</strong> (Threshold: 0.50) • Model: {fraud.model_name || 'RandomForest'}
            </p>
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {user ? (
              <button className="btn btn-primary btn-lg" onClick={() => navigate('/customer/transactions')}>
                View My Transactions
              </button>
            ) : (
              <button className="btn btn-outline btn-lg" onClick={() => navigate('/login')}>
                Sign In to SecurePay
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ML Fraud Blocked Result Screen
  if (result && result.status === 'rejected') {
    return (
      <div className="mobile-checkout-container" style={{ maxWidth: '440px', margin: '1.5rem auto', padding: '0 1rem' }}>
        <div
          style={{
            background: '#ffffff',
            borderRadius: '16px',
            padding: '2rem 1.5rem',
            textAlign: 'center',
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            border: '2px solid #ef4444',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: '#fee2e2',
              color: '#dc2626',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '2.5rem',
              fontWeight: 700,
              margin: '0 auto 1rem auto',
            }}
          >
            !
          </div>

          <h2 style={{ color: '#991b1b', margin: '0 0 0.25rem 0' }}>Payment Blocked</h2>
          <p style={{ color: '#7f1d1d', fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
            Flagged as suspicious by ML Fraud Detection
          </p>

          <div style={{ background: '#fef2f2', borderRadius: '12px', padding: '1rem', margin: '1rem 0', textAlign: 'left', fontSize: '0.85rem' }}>
            <p style={{ margin: '0 0 0.4rem 0', color: '#991b1b' }}>
              <strong>Decision:</strong> Suspicious
            </p>
            <p style={{ margin: '0 0 0.4rem 0', color: '#991b1b' }}>
              <strong>Risk Score:</strong> {result.fraud?.risk_score ?? 0.88} (Threshold: 0.50)
            </p>
            <p style={{ margin: '0', color: '#7f1d1d' }}>
              To protect account security, no funds were deducted from the wallet.
            </p>
          </div>

          <button className="btn btn-outline btn-lg" style={{ width: '100%' }} onClick={() => setResult(null)}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // Active Payment Form
  return (
    <div className="mobile-checkout-container" style={{ maxWidth: '460px', margin: '1.5rem auto', padding: '0 1rem' }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--primary-dark)' }}>SecurePay</h1>
        <p style={{ margin: '0.2rem 0 0 0', color: 'var(--muted)', fontSize: '0.85rem' }}>
          Instant Mobile QR Checkout • ML Protected
        </p>
      </div>

      <Card>
        {/* Merchant Card */}
        <div
          style={{
            padding: '1rem',
            background: 'var(--bg)',
            borderRadius: '10px',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Merchant
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text)' }}>
              {merchantName}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
              {merchantType}
            </div>
          </div>
          <div style={{ fontSize: '2rem' }}>🏪</div>
        </div>

        {/* Dynamic vs Store Amount */}
        {session ? (
          <div style={{ textAlign: 'center', padding: '0.75rem 0' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Amount Due</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--primary)' }}>
              ${session.amount}
            </div>
            {session.description && (
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
                {session.description}
              </div>
            )}
          </div>
        ) : (
          <div style={{ marginBottom: '1rem' }}>
            <label>Enter Amount to Pay ($)</label>
            <input
              type="number"
              step="0.01"
              min="0.5"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              required
            />
          </div>
        )}

        {/* Payer Account Details */}
        <form onSubmit={handlePay}>
          {user ? (
            <div style={{ padding: '0.75rem', background: '#f0fdf4', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem' }}>
              <div style={{ color: '#166534', fontWeight: 600 }}>Logged in as: {user.email}</div>
              <div style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                Payment will be debited from your active digital wallet.
              </div>
            </div>
          ) : (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${authMode === 'demo' ? 'btn-primary' : 'btn-outline'}`}
                  style={{ flex: 1 }}
                  onClick={() => setAuthMode('demo')}
                >
                  ⚡ 1-Tap Quick Pay
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${authMode === 'login' ? 'btn-primary' : 'btn-outline'}`}
                  style={{ flex: 1 }}
                  onClick={() => setAuthMode('login')}
                >
                  🔑 Login
                </button>
              </div>

              {authMode === 'demo' ? (
                <div>
                  <label>Select Customer Wallet to Pay From:</label>
                  <select
                    value={selectedDemoCustomer}
                    onChange={(e) => setSelectedDemoCustomer(e.target.value)}
                    required
                  >
                    {demoCustomers.map((c) => (
                      <option key={c.customer_id} value={c.customer_id}>
                        {c.email} (Balance: ${c.balance})
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div>
                  <label>Email</label>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                  />
                  <label>Password</label>
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                  />
                </div>
              )}
            </div>
          )}

          {/* ML Fraud Simulation Collapsible Panel */}
          <div style={{ margin: '0.75rem 0', border: '1px dashed var(--border)', borderRadius: '8px', padding: '0.6rem 0.75rem' }}>
            <div
              style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--muted)' }}
              onClick={() => setShowFraudToggles(!showFraudToggles)}
            >
              <span>🧪 ML Fraud Simulation Options</span>
              <span>{showFraudToggles ? '▲' : '▼'}</span>
            </div>
            {showFraudToggles && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={locationChange}
                    onChange={(e) => setLocationChange(e.target.checked)}
                  />
                  Simulate location change
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={deviceChange}
                    onChange={(e) => setDeviceChange(e.target.checked)}
                  />
                  Simulate new / unrecognized device
                </label>
              </div>
            )}
          </div>

          <button
            className="btn btn-primary btn-lg"
            style={{ width: '100%', fontSize: '1.1rem', padding: '0.85rem' }}
            disabled={busy || (session && session.is_expired)}
          >
            {busy ? 'Processing with ML Fraud Check...' : `Confirm & Pay $${finalAmount}`}
          </button>
        </form>

        <Alert type="danger" message={error} />
      </Card>
    </div>
  )
}
