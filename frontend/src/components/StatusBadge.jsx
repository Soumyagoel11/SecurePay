const COLORS = {
  success: 'badge-success',
  failed: 'badge-danger',
  rejected: 'badge-danger',
  pending: 'badge-warning',
  approved: 'badge-success',
  refunded: 'badge-info',
  Safe: 'badge-success',
  Suspicious: 'badge-danger',
  active: 'badge-success',
  frozen: 'badge-warning',
}

export default function StatusBadge({ status }) {
  const cls = COLORS[status] || 'badge-secondary'
  return <span className={`badge ${cls}`}>{status}</span>
}
