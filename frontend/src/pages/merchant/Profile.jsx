import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Loading from '../../components/Loading'

export default function MerchantProfile() {
  const [data, setData] = useState(null)
  useEffect(() => {
    api.get('/merchant/profile').then((r) => setData(r.data.data)).catch(() => {})
  }, [])
  if (!data) return <Loading />
  const { merchant, user } = data
  return (
    <div>
      <h2>Merchant Profile</h2>
      <Card>
        <p><strong>Company:</strong> {merchant.company_name}</p>
        <p><strong>Business Type:</strong> {merchant.business_type}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Merchant Risk Score:</strong> {merchant.merchant_risk}</p>
      </Card>
    </div>
  )
}
