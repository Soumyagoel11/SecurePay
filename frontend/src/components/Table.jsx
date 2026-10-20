export default function Table({ columns, rows, empty = 'No records found.' }) {
  if (!rows || rows.length === 0) {
    return <div className="empty-state">{empty}</div>
  }
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id || row.payment_id || row.user_id || i}>
              {columns.map((c) => (
                <td key={c.key}>
                  {c.render ? c.render(row[c.key], row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
