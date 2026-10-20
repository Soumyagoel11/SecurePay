import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function AdminFraudReports() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/admin/fraud-reports').then((r) => setRows(r.data.data.reports)).catch((e) => setError(e.message))
  }, [])
  if (error) return <div className="alert alert-danger">{error}</div>
  if (!rows) return <Loading />
  const columns = [
    { key: 'fraud_id', label: 'ID' },
    { key: 'payment_id', label: 'Payment' },
    { key: 'prediction', label: 'Decision', render: (v) => <StatusBadge status={v} /> },
    { key: 'risk_score', label: 'Risk Score' },
    { key: 'model_name', label: 'Model' },
    {
      key: 'payment',
      label: 'Amount',
      render: (v) => (v ? `$${v.amount}` : '-'),
    },
    { key: 'created_at', label: 'Detected' },
  ]
  return (
    <div>
      <h2>Fraud Reports</h2>
      <Card>
        <Table columns={columns} rows={rows} empty="No fraud reports yet." />
      </Card>
    </div>
  )
}
