import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'
import Alert from '../../components/Alert'

export default function PaymentDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get(`/payments/${id}`).then((r) => setData(r.data.data)).catch((e) => setError(e.message))
  }, [id])
  if (error) return <div className="alert alert-danger">{error}</div>
  if (!data) return <Loading />

  const payment = data.payment || data
  const fraud = data.fraud
  const transactions = data.transactions || []
  return (
    <div>
      <h2>Payment #{payment.payment_id}</h2>
      <Card>
        <p>Amount: <strong>${payment.amount}</strong></p>
        <p>Status: <StatusBadge status={payment.status} /></p>
        <p>Merchant ID: {payment.merchant_id}</p>
        <p>Fraud Decision: {fraud ? <StatusBadge status={fraud.prediction} /> : 'N/A'}</p>
        {fraud && <p>Risk Score: <strong>{fraud.risk_score}</strong></p>}
        {fraud && <p>Model: {fraud.model_name} ({fraud.model_version})</p>}
        {payment.failure_reason && <Alert type="danger" message={payment.failure_reason} />}
      </Card>
      <Card title="Ledger Entries">
        <Table
          columns={[
            { key: 'type', label: 'Type' },
            { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
            { key: 'status', label: 'Status' },
            { key: 'timestamp', label: 'Time' },
          ]}
          rows={transactions}
        />
      </Card>
      <button className="btn btn-outline" onClick={() => navigate('/customer/transactions')}>
        Back
      </button>
    </div>
  )
}
