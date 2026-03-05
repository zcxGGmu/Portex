import { Link } from 'react-router-dom'

import { PrimaryButton } from '../components/ui/PrimaryButton'

export function Register() {
  return (
    <div className="auth-page">
      <div className="panel auth-card">
        <h1 className="auth-title">Register</h1>
        <p className="auth-subtitle">
          Registration form will be connected in a later milestone.
        </p>
        <form className="form-stack">
          <div className="field">
            <label htmlFor="register-username">Username</label>
            <input disabled id="register-username" placeholder="Coming soon" />
          </div>
          <div className="field">
            <label htmlFor="register-password">Password</label>
            <input disabled id="register-password" placeholder="Coming soon" type="password" />
          </div>
          <PrimaryButton disabled type="button">
            Register (Soon)
          </PrimaryButton>
        </form>
        <p className="auth-footer muted">
          Already have an account? <Link to="/login">Back to sign in</Link>
        </p>
      </div>
    </div>
  )
}
