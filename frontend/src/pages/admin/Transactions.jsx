import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Loading from '../../components/Loading'

export default function AdminTransactions() {
  const [rows, setRows] = useState(null)
  useEffect(() => {
    api.get('/admin/transactions').then((r) => setRows(r.data.data.transactions)).catch(() => setRows([]))
  }, [])
  if (!rows) return <Loading />
  const columns = [
    { key: 'payment_id', label: 'ID' },
    { key: 'customer_id', label: 'Customer' },
    { key: 'merchant_id', label: 'Merchant' },
    { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    { key: 'fraud_decision', label: 'Risk', render: (v) => (v ? <StatusBadge status={v} /> : '-') },
    { key: 'payment_date', label: 'Date' },
  ]
  return (
    <div>
      <h2>All Transactions</h2>
      <Card>
        <Table columns={columns} rows={rows} />
      </Card>
    </div>
  )
}
