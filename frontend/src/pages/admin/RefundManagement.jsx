import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import StatusBadge from '../../components/StatusBadge'
import Alert from '../../components/Alert'
import Loading from '../../components/Loading'

export default function AdminRefundManagement() {
  const [rows, setRows] = useState(null)
  const [msg, setMsg] = useState({ type: '', text: '' })

  const load = () => api.get('/admin/refunds').then((r) => setRows(r.data.data.refunds)).catch(() => setRows([]))
  useEffect(() => { load() }, [])

  const act = async (id, action) => {
    setMsg({ type: '', text: '' })
    try {
      await api.put(`/refunds/${id}/${action}`)
      setMsg({ type: 'success', text: `Refund ${action}d` })
      load()
    } catch (e) {
      setMsg({ type: 'danger', text: e.message })
    }
  }

  if (!rows) return <Loading />
  const columns = [
    { key: 'refund_id', label: 'ID' },
    { key: 'payment_id', label: 'Payment' },
    { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
    { key: 'reason', label: 'Reason' },
    { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
    {
      key: 'actions',
      label: 'Actions',
      render: (v, row) =>
        row.status === 'pending' ? (
          <>
            <button className="btn btn-success btn-sm" onClick={() => act(row.refund_id, 'approve')}>
              Approve
            </button>{' '}
            <button className="btn btn-danger btn-sm" onClick={() => act(row.refund_id, 'reject')}>
              Reject
            </button>
          </>
        ) : (
          '-'
        ),
    },
  ]
  return (
    <div>
      <h2>Refund Management</h2>
      <Card>
        <Alert type={msg.type} message={msg.text} />
        <Table columns={columns} rows={rows} empty="No refund requests." />
      </Card>
    </div>
  )
}
