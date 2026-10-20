import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import Loading from '../../components/Loading'

export default function AdminUsers() {
  const [rows, setRows] = useState(null)
  useEffect(() => {
    api.get('/admin/users').then((r) => setRows(r.data.data.users)).catch(() => setRows([]))
  }, [])
  if (!rows) return <Loading />
  const columns = [
    { key: 'user_id', label: 'ID' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role' },
    { key: 'created_at', label: 'Joined' },
  ]
  return (
    <div>
      <h2>Users</h2>
      <Card>
        <Table columns={columns} rows={rows} />
      </Card>
    </div>
  )
}
