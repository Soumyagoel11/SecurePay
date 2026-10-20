import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Alert from '../../components/Alert'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function MakePayment() {
  const [tab, setTab] = useState('manual') // 'manual' or 'qr'
  const [merchants, setMerchants] = useState([])
  const [merchantId, setMerchantId] = useState('')
  const [amount, setAmount] = useState('')
  const [locationChange, setLocationChange] = useState(false)
  const [deviceChange, setDeviceChange] = useState(false)

  // QR Payment Tab
  const [qrInput, setQrInput] = useState('')
  const [qrSession, setQrSession] = useState(null)
  const [qrLoading, setQrLoading] = useState(false)

  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/customer/merchants').then((r) => setMerchants(r.data.data.merchants)).catch(() => {})
  }, [])

  const submitManual = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setBusy(true)
    try {
      const res = await api.post('/payments', {
        merchant_id: Number(merchantId),
        amount: Number(amount),
        location_change: locationChange ? 1 : 0,
        device_change: deviceChange ? 1 : 0,
      })
      setResult(res.data.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  // Lookup QR Token or URL
  const lookupQr = async (e) => {
    if (e) e.preventDefault()
    setError('')
    setQrSession(null)
    let token = qrInput.trim()
    if (token.includes('/pay/qr/')) {
      token = token.split('/pay/qr/')[1].split('?')[0].split('/')[0]
    }
    if (!token) {
      setError('Please enter a valid QR payment token or URL')
      return
    }

    setQrLoading(true)
    try {
      const res = await api.get(`/qr-payments/${token}`)
      setQrSession(res.data.data)
    } catch (err) {
      setError(err.message || 'QR session not found or expired')
    } finally {
      setQrLoading(false)
    }
  }

  // Pay the retrieved QR session
  const submitQrPay = async (e) => {
    e.preventDefault()
    if (!qrSession) return
    setError('')
    setResult(null)
    setBusy(true)
    try {
      const res = await api.post(`/qr-payments/${qrSession.token}/pay`, {
        location_change: locationChange ? 1 : 0,
        device_change: deviceChange ? 1 : 0,
      })
      setResult(res.data.data)
      setQrSession(null)
      setQrInput('')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h2>Make a Payment</h2>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <button
          className={`btn ${tab === 'manual' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => { setTab('manual'); setResult(null); setError('') }}
        >
          Select Merchant
        </button>
        <button
          className={`btn ${tab === 'qr' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => { setTab('qr'); setResult(null); setError('') }}
        >
          📷 Pay via QR Code / Link
        </button>
      </div>

      {tab === 'manual' ? (
        <Card title="Direct Payment">
          <form onSubmit={submitManual}>
            <label>Select Merchant</label>
            <select value={merchantId} onChange={(e) => setMerchantId(e.target.value)} required>
              <option value="">-- choose --</option>
              {merchants.map((m) => (
                <option key={m.merchant_id} value={m.merchant_id}>
                  {m.company_name} ({m.business_type})
                </option>
              ))}
            </select>
            <label>Amount ($)</label>
            <input type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            <label className="checkbox">
              <input type="checkbox" checked={locationChange} onChange={(e) => setLocationChange(e.target.checked)} />
              Location changed from usual
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={deviceChange} onChange={(e) => setDeviceChange(e.target.checked)} />
              New device used
            </label>
            <button className="btn btn-primary" disabled={busy || !merchantId}>
              {busy ? 'Processing...' : 'Pay'}
            </button>
          </form>
          <Alert type="danger" message={error} />
        </Card>
      ) : (
        <Card title="Pay via QR Code or Link">
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
            Enter the payment token or paste the URL generated from the Merchant QR Terminal.
          </p>
          <form onSubmit={lookupQr} className="inline-form" style={{ marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="e.g. 7f8a9b... or http://.../pay/qr/token"
              value={qrInput}
              onChange={(e) => setQrInput(e.target.value)}
              required
            />
            <button className="btn btn-primary" disabled={qrLoading}>
              {qrLoading ? 'Fetching...' : 'Lookup QR'}
            </button>
          </form>

          {qrSession && (
            <div style={{ background: 'var(--bg)', borderRadius: '8px', padding: '1rem', marginTop: '1rem' }}>
              <h4>Payment Request Details</h4>
              <p><strong>Merchant:</strong> {qrSession.merchant_name} ({qrSession.merchant_type})</p>
              <p><strong>Amount:</strong> <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)' }}>${qrSession.amount}</span></p>
              <p><strong>Description:</strong> {qrSession.description}</p>
              <p><strong>Status:</strong> <StatusBadge status={qrSession.status} /></p>

              {qrSession.status === 'pending' && !qrSession.is_expired ? (
                <form onSubmit={submitQrPay} style={{ marginTop: '0.75rem' }}>
                  <label className="checkbox">
                    <input type="checkbox" checked={locationChange} onChange={(e) => setLocationChange(e.target.checked)} />
                    Simulate location change
                  </label>
                  <label className="checkbox">
                    <input type="checkbox" checked={deviceChange} onChange={(e) => setDeviceChange(e.target.checked)} />
                    Simulate new device
                  </label>
                  <button className="btn btn-success" disabled={busy} style={{ marginTop: '0.5rem' }}>
                    {busy ? 'Processing...' : `Confirm & Pay $${qrSession.amount}`}
                  </button>
                </form>
              ) : (
                <Alert type="danger" message={`Cannot pay: session is ${qrSession.status}`} />
              )}
            </div>
          )}

          <Alert type="danger" message={error} />
        </Card>
      )}

      {result && (
        <Card title="Payment Result">
          <p>Status: <StatusBadge status={result.status} /></p>
          <p>{result.message}</p>
          {result.payment && (
            <p>Payment ID: <strong>#{result.payment.payment_id}</strong> • Amount: <strong>${result.payment.amount}</strong></p>
          )}
          {result.fraud && (
            <div className="fraud-box">
              <h4>Fraud Analysis</h4>
              <p>Decision: <StatusBadge status={result.fraud.prediction} /></p>
              <p>Risk Score: <strong>{result.fraud.risk_score}</strong></p>
              <p>Model: {result.fraud.model_name} ({result.fraud.model_version})</p>
            </div>
          )}
          <button className="btn btn-outline" onClick={() => navigate('/customer/transactions')}>
            View Transactions
          </button>
        </Card>
      )}
    </div>
  )
}
