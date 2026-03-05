import type { FormEvent } from 'react'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import { useAuthStore } from '../stores/auth'

interface LoginLocationState {
  from?: string
}

export function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((state) => state.login)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)

    if (!username.trim() || !password) {
      setErrorMessage('Username and password are required.')
      return
    }

    setIsSubmitting(true)
    try {
      await login(username.trim(), password)
      const state = location.state as LoginLocationState | null
      navigate(state?.from ?? '/chat', { replace: true })
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('Unable to login. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="panel auth-card">
        <h1 className="auth-title">Sign In</h1>
        <p className="auth-subtitle">Use your Portex account to continue.</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              autoComplete="username"
              id="username"
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter username"
              value={username}
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              autoComplete="current-password"
              id="password"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              type="password"
              value={password}
            />
          </div>
          {errorMessage ? <p className="error-text">{errorMessage}</p> : null}
          <PrimaryButton disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </PrimaryButton>
        </form>
        <p className="auth-footer muted">
          No account yet? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  )
}
