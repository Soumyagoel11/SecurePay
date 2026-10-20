import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  return (
    <nav className="navbar">
      <div className="navbar-brand" onClick={() => (window.location.href = '/')}>
        🔒 SecurePay
      </div>
      <div className="navbar-links">
        {user ? (
          <>
            <span className="navbar-user">
              {user.email} <span className="role-pill">{user.role}</span>
            </span>
            <button className="btn btn-outline" onClick={logout}>
              Logout
            </button>
          </>
        ) : (
          <>
            <a className="btn btn-outline" href="/login">Login</a>
            <a className="btn btn-primary" href="/register">Register</a>
          </>
        )}
      </div>
    </nav>
  )
}
