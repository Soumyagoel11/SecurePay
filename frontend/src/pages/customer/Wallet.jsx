import { useEffect, useState } from 'react'
import api from '../../services/api'
import { Card } from '../../components/Card'
import Table from '../../components/Table'
import Loading from '../../components/Loading'
import Alert from '../../components/Alert'

export default function CustomerWallet() {
  const [wallet, setWallet] = useState(null)
  const [amount, setAmount] = useState('')
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [busy, setBusy] = useState(false)

  const load = () => api.get('/wallet').then((r) => setWallet(r.data.data.wallet))
  useEffect(() => { load().catch(() => {}) }, [])

  const addMoney = async (e) => {
    e.preventDefault()
    setBusy(true)
    setMsg({ type: '', text: '' })
    try {
      const res = await api.post('/wallet/add-money', { amount: Number(amount) })
      setWallet(res.data.data.wallet)
      setMsg({ type: 'success', text: 'Money added successfully' })
      setAmount('')
    } catch (err) {
      setMsg({ type: 'danger', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  if (!wallet) return <Loading />
  return (
    <div>
      <h2>My Wallet</h2>
      <Card title={`Balance: $${wallet.balance}`}>
        <p>Status: {wallet.status}</p>
        <form className="inline-form" onSubmit={addMoney}>
          <input
            type="number"
            min="1"
            placeholder="Amount to add"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
          <button className="btn btn-primary" disabled={busy}>
            {busy ? 'Adding...' : 'Add Money (Demo)'}
          </button>
        </form>
        <Alert type={msg.type} message={msg.text} />
      </Card>
      <WalletTransactions />
    </div>
  )
}

function WalletTransactions() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api.get('/wallet/transactions').then((r) => setRows(r.data.data.transactions)).catch(() => setRows([]))
  }, [])
  const columns = [
    { key: 'type', label: 'Type' },
    { key: 'amount', label: 'Amount', render: (v) => `$${v}` },
    { key: 'status', label: 'Status' },
    { key: 'timestamp', label: 'Time' },
  ]
  return (
    <Card title="Wallet Transactions">
      <Table columns={columns} rows={rows} />
    </Card>
  )
}
