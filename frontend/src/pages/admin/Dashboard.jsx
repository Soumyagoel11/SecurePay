import { useEffect, useState } from 'react'
import api from '../../services/api'
import { StatCard, Card } from '../../components/Card'
import Loading from '../../components/Loading'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/admin/dashboard').then((r) => setStats(r.data.data.stats)).catch((e) => setError(e.message))
  }, [])
  if (error) return <div className="alert alert-danger">{error}</div>
  if (!stats) return <Loading />
  return (
    <div>
      <h2>Admin Dashboard</h2>
      <div className="stats-grid">
        <StatCard title="Total Users" value={stats.total_users} accent="accent-blue" />
        <StatCard title="Customers" value={stats.total_customers} accent="accent-green" />
        <StatCard title="Merchants" value={stats.total_merchants} accent="accent-purple" />
        <StatCard title="Transactions" value={stats.total_transactions} accent="accent-blue" />
        <StatCard title="Successful" value={stats.successful_payments} accent="accent-green" />
        <StatCard title="Suspicious" value={stats.suspicious_transactions} accent="accent-red" />
        <StatCard title="Pending Refunds" value={stats.pending_refund_requests} accent="accent-orange" />
        <StatCard title="Total Refunds" value={stats.total_refunds} accent="accent-purple" />
      </div>
      <Card>
        <p>Use the sidebar to manage users, merchants, transactions, fraud reports and refunds.</p>
      </Card>
    </div>
  )
}
