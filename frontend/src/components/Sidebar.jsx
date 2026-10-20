import { useAuth } from '../context/AuthContext'

const LINKS = {
  customer: [
    { to: '/customer', label: 'Dashboard' },
    { to: '/customer/wallet', label: 'Wallet' },
    { to: '/customer/pay', label: 'Make Payment' },
    { to: '/customer/transactions', label: 'Transactions' },
    { to: '/customer/refund', label: 'Request Refund' },
    { to: '/customer/profile', label: 'Profile' },
  ],
  merchant: [
    { to: '/merchant', label: 'Dashboard' },
    { to: '/merchant/qr-terminal', label: '⚡ QR Terminal' },
    { to: '/merchant/payments', label: 'Received Payments' },
    { to: '/merchant/transactions', label: 'Transactions' },
    { to: '/merchant/suspicious', label: 'Suspicious' },
    { to: '/merchant/profile', label: 'Profile' },
  ],
  admin: [
    { to: '/admin', label: 'Dashboard' },
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/merchants', label: 'Merchants' },
    { to: '/admin/transactions', label: 'Transactions' },
    { to: '/admin/fraud', label: 'Fraud Reports' },
    { to: '/admin/refunds', label: 'Refund Management' },
  ],
}

export default function Sidebar() {
  const { user } = useAuth()
  if (!user) return null
  const links = LINKS[user.role] || []
  return (
    <aside className="sidebar">
      <ul>
        {links.map((l) => (
          <li key={l.to}>
            <a href={l.to}>{l.label}</a>
          </li>
        ))}
      </ul>
    </aside>
  )
}
