import { useAuth } from '../context/AuthContext'

export default function Landing() {
  const { user } = useAuth()
  const cta = user
    ? user.role === 'admin'
      ? '/admin'
      : user.role === 'merchant'
      ? '/merchant'
      : '/customer'
    : '/register'
  return (
    <div className="landing">
      <section className="hero">
        <h1>SecurePay</h1>
        <p className="tagline">
          A digital payment gateway with built-in Machine Learning fraud detection.
        </p>
        <div className="hero-actions">
          <a className="btn btn-primary btn-lg" href={cta}>
            {user ? 'Go to Dashboard' : 'Get Started'}
          </a>
          <a className="btn btn-outline btn-lg" href="/login">
            Login
          </a>
        </div>
      </section>
      <section className="features">
        <div className="card feature">
          <h3>💳 Digital Wallet</h3>
          <p>Customers maintain balances, top up, and pay merchants instantly.</p>
        </div>
        <div className="card feature">
          <h3>🤖 ML Fraud Detection</h3>
          <p>Every transaction is scored by a trained model with a risk score.</p>
        </div>
        <div className="card feature">
          <h3>🛡️ Role-Based Access</h3>
          <p>Separate dashboards and permissions for customers, merchants, admins.</p>
        </div>
      </section>
    </div>
  )
}
