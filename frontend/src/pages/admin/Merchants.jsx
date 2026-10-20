import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import Loading from '../../components/Loading'

export default function AdminMerchants() {
  const [rows, setRows] = useState(null)
  useEffect(() => {
    api.get('/admin/merchants').then((r) => setRows(r.data.data.merchants)).catch(() => setRows([]))
  }, [])
  if (!rows) return <Loading />
  const columns = [
    { key: 'merchant_id', label: 'ID' },
    { key: 'company_name', label: 'Company' },
    { key: 'business_type', label: 'Type' },
    { key: 'merchant_risk', label: 'Risk' },
    { key: 'email', label: 'Email' },
  ]
  return (
    <div>
      <h2>Merchants</h2>
      <Card>
        <Table columns={columns} rows={rows} />
      </Card>
    </div>
  )
}
