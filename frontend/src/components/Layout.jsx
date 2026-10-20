import Navbar from './Navbar'
import Sidebar from './Sidebar'
import Loading from './Loading'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Loading message="Initializing..." />
  return (
    <div className="app-shell">
      <Navbar />
      <div className="app-body">
        {user && <Sidebar />}
        <main className="content">{children}</main>
      </div>
    </div>
  )
}
