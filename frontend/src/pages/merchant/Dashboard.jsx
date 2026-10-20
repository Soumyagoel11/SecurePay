import { useEffect, useState } from 'react'
import api from '../../services/api'
import { StatCard, Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function MerchantDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/merchant/dashboard').then((r) => setData(r.data.data)).catch((e) => setError(e.message))
  }, [])
  if (error) return <div className="alert alert-danger">{error}</div>
  if (!data) return <Loading />

  const { stats, recent_transactions } = data
  const columns = [
    { key: 'payment_id', label: 'ID' },
    { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'fraud_decision', label: 'Risk', render: (v) => (v ? <StatusBadge status={v} /> : '-') },
    { key: 'payment_date', label: 'Date' },
  ]
  return (
    <div>
      <h2>Merchant Dashboard</h2>
      <div className="stats-grid">
        <StatCard title="Total Revenue" value={`$${stats.total_revenue}`} accent="accent-green" />
        <StatCard title="Total Payments" value={stats.total_payments} accent="accent-blue" />
        <StatCard title="Successful" value={stats.successful_payments} accent="accent-green" />
        <StatCard title="Suspicious" value={stats.suspicious_payments} accent="accent-red" />
      </div>
      <Card title="Recent Transactions">
        <Table columns={columns} rows={recent_transactions} />
      </Card>
    </div>
  )
}
