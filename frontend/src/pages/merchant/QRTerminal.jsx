import { useState, useEffect, useRef } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Alert from '../../components/Alert'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function MerchantQRTerminal() {
  const [profile, setProfile] = useState(null)
  const [networkInfo, setNetworkInfo] = useState({ lan_ip: '127.0.0.1', frontend_port: 3000 })
  const [hostMode, setHostMode] = useState('lan') // 'lan' or 'localhost' or 'custom'
  const [customHost, setCustomHost] = useState('')
  const [activeTab, setActiveTab] = useState('dynamic') // 'dynamic' or 'store'

  // Dynamic QR form
  const [amount, setAmount] = useState('50.00')
  const [description, setDescription] = useState('Order #101 - In-store')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // Active Session
  const [currentSession, setCurrentSession] = useState(null)
  const [liveStatus, setLiveStatus] = useState(null)
  const [paymentResult, setPaymentResult] = useState(null)
  const pollTimerRef = useRef(null)

  // Fetch Merchant & Network info
  useEffect(() => {
    api.get('/merchant/profile').then((r) => setProfile(r.data.data)).catch(() => {})
    api.get('/qr-payments/network-info').then((r) => {
      setNetworkInfo(r.data.data)
    }).catch(() => {})
  }, [])

  // Resolve base URL for QR codes
  const getBaseUrl = () => {
    if (hostMode === 'lan' && networkInfo.lan_ip) {
      return `http://${networkInfo.lan_ip}:${networkInfo.frontend_port || 3000}`
    }
    if (hostMode === 'custom' && customHost) {
      return customHost.replace(/\/$/, '')
    }
    return window.location.origin
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    }
  }, [])

  // Poll for QR status
  const startPolling = (token) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/qr-payments/${token}/status`)
        const data = res.data.data
        setLiveStatus(data.status)
        if (data.status === 'completed' || data.status === 'rejected') {
          clearInterval(pollTimerRef.current)
          pollTimerRef.current = null
          if (data.payment) {
            setPaymentResult({
              status: data.status,
              payment: data.payment,
              fraud: data.fraud,
            })
          }
        }
      } catch (e) {
        // network glitch or polling error
      }
    }, 1500)
  }

  const createQR = async (e) => {
    if (e) e.preventDefault()
    setError('')
    setPaymentResult(null)
    setLiveStatus('pending')
    setBusy(true)

    try {
      const hostBase = getBaseUrl()
      const res = await api.post('/qr-payments/create', {
        amount: Number(amount),
        description,
        host_base: hostBase,
        expires_in_minutes: 15,
      })
      const qrData = res.data.data
      setCurrentSession(qrData)
      startPolling(qrData.qr.token)
    } catch (err) {
      setError(err.message || 'Failed to create QR payment session')
    } finally {
      setBusy(false)
    }
  }

  const resetTerminal = () => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    setCurrentSession(null)
    setLiveStatus(null)
    setPaymentResult(null)
    setError('')
  }

  if (!profile) return <Loading />

  const { merchant } = profile
  const merchantStoreUrl = `${getBaseUrl()}/pay/merchant/${merchant.merchant_id}`
  const dynamicPayUrl = currentSession ? `${getBaseUrl()}/pay/qr/${currentSession.qr.token}` : ''

  return (
    <div className="qr-terminal-page">
      <div className="page-header" style={{ marginBottom: '1.25rem' }}>
        <h2>QR Payment Terminal (POS)</h2>
        <p style={{ color: 'var(--muted)', margin: '0.25rem 0 0 0' }}>
          Generate instant QR codes scannable with <strong>Google Lens</strong> or any mobile camera to accept payments in real time.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <button
          className={`btn ${activeTab === 'dynamic' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('dynamic')}
        >
          Dynamic Order QR (Specific Amount)
        </button>
        <button
          className={`btn ${activeTab === 'store' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('store')}
        >
          Permanent Store QR Code
        </button>
      </div>

      {/* Network Host Settings Bar */}
      <Card>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
          <div>
            <strong>Network Mode for Phone / Google Lens:</strong>
            <span style={{ marginLeft: '0.5rem', color: 'var(--muted)', fontSize: '0.85rem' }}>
              (Phones scanning with Google Lens need the LAN IP to connect)
            </span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              className={`btn btn-sm ${hostMode === 'lan' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setHostMode('lan')}
              title="Best for phones scanning with Google Lens on same Wi-Fi"
            >
              LAN Wi-Fi ({networkInfo.lan_ip})
            </button>
            <button
              className={`btn btn-sm ${hostMode === 'localhost' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setHostMode('localhost')}
              title="For testing in another tab on this computer"
            >
              Localhost
            </button>
            <button
              className={`btn btn-sm ${hostMode === 'custom' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setHostMode('custom')}
            >
              Custom IP
            </button>
          </div>
        </div>
        {hostMode === 'custom' && (
          <div style={{ marginTop: '0.75rem' }}>
            <input
              placeholder="e.g. http://192.168.1.50:3000"
              value={customHost}
              onChange={(e) => setCustomHost(e.target.value)}
              style={{ maxWidth: '350px' }}
            />
          </div>
        )}
      </Card>

      {activeTab === 'dynamic' ? (
        <div className="terminal-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
          {/* Left: Input Form */}
          <Card title="New Payment Request">
            <form onSubmit={createQR}>
              <label>Amount ($)</label>
              <input
                type="number"
                step="0.01"
                min="0.5"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                disabled={busy}
              />

              <label>Order / Bill Note</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Order #101, Table 4"
                disabled={busy}
              />

              <div style={{ marginTop: '0.75rem' }}>
                <button className="btn btn-primary btn-lg" style={{ width: '100%' }} disabled={busy}>
                  {busy ? 'Generating...' : '⚡ Generate Payment QR Code'}
                </button>
              </div>
            </form>
            <Alert type="danger" message={error} />

            <div style={{ marginTop: '1.25rem', padding: '0.75rem', background: 'var(--bg)', borderRadius: '8px', fontSize: '0.85rem' }}>
              <strong>How it works:</strong>
              <ol style={{ paddingLeft: '1.25rem', margin: '0.5rem 0 0 0', lineHeight: 1.6 }}>
                <li>Generate QR code for the desired amount.</li>
                <li>Customer scans with <strong>Google Lens</strong> or phone camera.</li>
                <li>Customer views and approves payment on their device.</li>
                <li>This web terminal instantly updates with <strong>"Payment Received"</strong>!</li>
              </ol>
            </div>
          </Card>

          {/* Right: Active QR Code & Live Status */}
          <Card title="Live Customer Screen">
            {currentSession ? (
              <div style={{ textAlign: 'center', padding: '0.5rem 0' }}>
                {/* Payment Successful Result Screen */}
                {paymentResult && paymentResult.status === 'success' ? (
                  <div className="payment-success-card" style={{ padding: '1.5rem', background: '#f0fdf4', border: '2px solid var(--green)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '3rem', color: 'var(--green)', lineHeight: 1 }}>✓</div>
                    <h3 style={{ color: '#166534', margin: '0.5rem 0' }}>Payment Received!</h3>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: '#166534', margin: '0.5rem 0' }}>
                      ${paymentResult.payment.amount}
                    </div>
                    <p style={{ color: 'var(--muted)', margin: '0.25rem 0' }}>
                      Payment ID: <strong>#{paymentResult.payment.payment_id}</strong>
                    </p>
                    <p style={{ color: 'var(--muted)', margin: '0.25rem 0' }}>
                      Customer ID: <strong>{paymentResult.payment.customer_id}</strong>
                    </p>

                    {paymentResult.fraud && (
                      <div className="fraud-box" style={{ background: '#ffffff', margin: '1rem 0', textAlign: 'left', border: '1px solid #bbf7d0' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: '#166534' }}>🛡️ ML Fraud Gate Verification</h4>
                        <p style={{ margin: '0.2rem 0' }}>Decision: <StatusBadge status={paymentResult.fraud.prediction} /></p>
                        <p style={{ margin: '0.2rem 0' }}>Risk Score: <strong>{paymentResult.fraud.risk_score}</strong> (Safe &lt; 0.5)</p>
                        <p style={{ margin: '0.2rem 0' }}>Model: {paymentResult.fraud.model_name}</p>
                      </div>
                    )}

                    <button className="btn btn-primary btn-lg" style={{ marginTop: '1rem', width: '100%' }} onClick={resetTerminal}>
                      Accept Next Payment
                    </button>
                  </div>
                ) : paymentResult && paymentResult.status === 'rejected' ? (
                  <div className="payment-rejected-card" style={{ padding: '1.5rem', background: '#fef2f2', border: '2px solid var(--red)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '3rem', color: 'var(--red)', lineHeight: 1 }}>⚠</div>
                    <h3 style={{ color: '#991b1b', margin: '0.5rem 0' }}>Transaction Blocked by ML</h3>
                    <p style={{ color: '#7f1d1d' }}>
                      The ML Fraud Detection system scored this transaction as high risk.
                    </p>
                    {paymentResult.fraud && (
                      <div className="fraud-box" style={{ background: '#ffffff', margin: '1rem 0', textAlign: 'left', border: '1px solid #fecaca' }}>
                        <p style={{ margin: '0.2rem 0' }}>Risk Score: <strong>{paymentResult.fraud.risk_score}</strong></p>
                        <p style={{ margin: '0.2rem 0' }}>Zero funds were transferred.</p>
                      </div>
                    )}
                    <button className="btn btn-outline" style={{ marginTop: '1rem' }} onClick={resetTerminal}>
                      Reset Terminal
                    </button>
                  </div>
                ) : (
                  <div>
                    {/* Live Waiting QR Code */}
                    <div
                      style={{
                        background: '#ffffff',
                        padding: '1.25rem',
                        display: 'inline-block',
                        borderRadius: '12px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                        border: '1px solid var(--border)',
                      }}
                    >
                      <QRCodeSVG
                        value={dynamicPayUrl}
                        size={240}
                        level="H"
                        includeMargin={true}
                      />
                    </div>

                    <div style={{ marginTop: '0.75rem' }}>
                      <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)' }}>
                        ${currentSession.qr.amount}
                      </span>
                      <p style={{ margin: '0.25rem 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
                        {currentSession.qr.description}
                      </p>
                    </div>

                    {/* Animated Pulsing Status */}
                    <div
                      style={{
                        margin: '1rem auto',
                        padding: '0.6rem 1rem',
                        background: '#eff6ff',
                        borderRadius: '999px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        color: 'var(--primary-dark)',
                        fontWeight: 600,
                        fontSize: '0.9rem',
                      }}
                    >
                      <span className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }} />
                      Waiting for scan & payment...
                    </div>

                    <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                      <a
                        href={dynamicPayUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-outline btn-sm"
                        title="Simulate scanning on mobile device"
                      >
                        📱 Open / Simulate Scan
                      </a>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => {
                          navigator.clipboard.writeText(dynamicPayUrl)
                          alert('Payment URL copied!')
                        }}
                      >
                        📋 Copy Link
                      </button>
                      <button className="btn btn-sm" style={{ background: '#e2e8f0' }} onClick={resetTerminal}>
                        Cancel
                      </button>
                    </div>

                    <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.75rem', wordBreak: 'break-all' }}>
                      {dynamicPayUrl}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--muted)' }}>
                <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📷</div>
                <h4>No Active QR Code</h4>
                <p>Fill in an amount on the left and click <strong>Generate Payment QR Code</strong>.</p>
              </div>
            )}
          </Card>
        </div>
      ) : (
        /* Permanent Store QR Code */
        <Card title={`Store QR Code: ${merchant.company_name}`}>
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <p style={{ color: 'var(--muted)', marginBottom: '1rem' }}>
              Place this QR stand at your billing counter. Customers can scan it with Google Lens to enter any amount and pay you directly.
            </p>
            <div
              style={{
                background: '#ffffff',
                padding: '1.5rem',
                display: 'inline-block',
                borderRadius: '16px',
                boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
                border: '1px solid var(--border)',
              }}
            >
              <QRCodeSVG
                value={merchantStoreUrl}
                size={260}
                level="H"
                includeMargin={true}
              />
              <h3 style={{ margin: '0.75rem 0 0.25rem 0', color: 'var(--text)' }}>{merchant.company_name}</h3>
              <span className="badge badge-info">{merchant.business_type}</span>
            </div>

            <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <a href={merchantStoreUrl} target="_blank" rel="noreferrer" className="btn btn-primary">
                📱 Open Store Checkout Page
              </a>
              <button
                className="btn btn-outline"
                onClick={() => {
                  navigator.clipboard.writeText(merchantStoreUrl)
                  alert('Store link copied!')
                }}
              >
                📋 Copy Store Link
              </button>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.75rem' }}>
              {merchantStoreUrl}
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}
