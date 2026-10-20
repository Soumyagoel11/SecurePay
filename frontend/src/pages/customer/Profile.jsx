import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Loading from '../../components/Loading'

export default function CustomerProfile() {
  const [data, setData] = useState(null)
  useEffect(() => {
    api.get('/customer/profile').then((r) => setData(r.data.data)).catch(() => {})
  }, [])
  if (!data) return <Loading />
  const { customer, user, wallet } = data
  return (
    <div>
      <h2>My Profile</h2>
      <Card>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.role}</p>
        <p><strong>Phone:</strong> {customer.phone || '-'}</p>
        <p><strong>Address:</strong> {customer.address || '-'}</p>
        <p><strong>Age:</strong> {customer.customer_age || '-'}</p>
        <p><strong>Wallet Balance:</strong> ${wallet ? wallet.balance : 0}</p>
      </Card>
    </div>
  )
}
