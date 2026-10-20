import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function CustomerTransactions() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/payments').then((r) => setRows(r.data.data.payments)).catch((e) => setError(e.message))
  }, [])
  if (error) return <div className="alert alert-danger">{error}</div>
  if (!rows) return <Loading />

  const columns = [
    { key: 'payment_id', label: 'ID', render: (v) => <Link to={`/customer/transactions/${v}`}>{v}</Link> },
    { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'fraud_decision', label: 'Risk', render: (v) => (v ? <StatusBadge status={v} /> : '-') },
    { key: 'risk_score', label: 'Risk Score' },
    { key: 'payment_date', label: 'Date' },
  ]
  return (
    <div>
      <h2>My Transactions</h2>
      <Card>
        <Table columns={columns} rows={rows} />
      </Card>
    </div>
  )
}
