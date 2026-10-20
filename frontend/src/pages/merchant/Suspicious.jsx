import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function MerchantSuspicious() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/merchant/suspicious').then((r) => setRows(r.data.data.suspicious)).catch((e) => setError(e.message))
  }, [])
  if (error) return <div className="alert alert-danger">{error}</div>
  if (!rows) return <Loading />
  const columns = [
    { key: 'fraud_id', label: 'Fraud ID' },
    { key: 'payment_id', label: 'Payment' },
    { key: 'prediction', label: 'Decision', render: (v) => <StatusBadge status={v} /> },
    { key: 'risk_score', label: 'Risk Score' },
    {
      key: 'payment',
      label: 'Amount',
      render: (v) => (v ? `$${v.amount}` : '-'),
    },
    { key: 'created_at', label: 'Detected' },
  ]
  return (
    <div>
      <h2>Suspicious Transactions</h2>
      <Card>
        <Table columns={columns} rows={rows} empty="No suspicious transactions. 🎉" />
      </Card>
    </div>
  )
}
