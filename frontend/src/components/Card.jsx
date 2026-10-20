export function StatCard({ title, value, icon, accent }) {
  return (
    <div className={`card stat-card ${accent || ''}`}>
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
      {icon && <div className="stat-icon">{icon}</div>}
    </div>
  )
}

export function Card({ title, children, className = '' }) {
  return (
    <div className={`card ${className}`}>
      {title && <div className="card-header">{title}</div>}
      <div className="card-body">{children}</div>
    </div>
  )
}
