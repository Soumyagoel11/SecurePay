import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Alert from '../../components/Alert'
import Loading from '../../components/Loading'

export default function RefundRequest() {
  const [payments, setPayments] = useState([])
  const [refunds, setRefunds] = useState([])
  const [paymentId, setPaymentId] = useState('')
  const [reason, setReason] = useState('')
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [busy, setBusy] = useState(false)

  const load = () => {
    api.get('/payments').then((r) => setPayments(r.data.data.payments.filter((p) => p.status === 'success')))
    api.get('/refunds').then((r) => setRefunds(r.data.data.refunds)).catch(() => {})
  }
  useEffect(() => { load() }, [])

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setMsg({ type: '', text: '' })
    try {
      await api.post('/refunds', { payment_id: Number(paymentId), reason })
      setMsg({ type: 'success', text: 'Refund request submitted' })
      setPaymentId('')
      setReason('')
      load()
    } catch (err) {
      setMsg({ type: 'danger', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  if (!payments) return <Loading />
  const columns = [
    { key: 'refund_id', label: 'Refund ID' },
    { key: 'payment_id', label: 'Payment' },
    { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'created_at', label: 'Requested' },
  ]
  return (
    <div>
      <h2>Request a Refund</h2>
      <Card title="Your Successful Payments">
        {payments.length === 0 ? (
          <p>No successful payments available for refund.</p>
        ) : (
          <form onSubmit={submit}>
            <label>Select Payment</label>
            <select value={paymentId} onChange={(e) => setPaymentId(e.target.value)} required>
              <option value="">-- choose --</option>
              {payments.map((p) => (
                <option key={p.payment_id} value={p.payment_id}>
                  #{p.payment_id} - ${p.amount}
                </option>
              ))}
            </select>
            <label>Reason</label>
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for refund" />
            <button className="btn btn-primary" disabled={busy || !paymentId}>
              {busy ? 'Submitting...' : 'Request Refund'}
            </button>
          </form>
        )}
        <Alert type={msg.type} message={msg.text} />
      </Card>
      <Card title="Refund Status">
        <Table columns={columns} rows={refunds} />
      </Card>
    </div>
  )
}
