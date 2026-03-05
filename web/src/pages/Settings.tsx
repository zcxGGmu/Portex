import { AppLayout } from '../components/layout/AppLayout'
import { useCurrentUserQuery } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

export function Settings() {
  const storedUser = useAuthStore((state) => state.currentUser)
  const token = useAuthStore((state) => state.token)
  const { data, isLoading } = useCurrentUserQuery()
  const currentUser = data ?? storedUser
  const tokenPreview = token ? `${token.slice(0, 24)}...` : 'Not available'

  return (
    <AppLayout title="Settings">
      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Account</h2>
        <div className="settings-grid">
          <div className="stat-card">
            <strong>Username</strong>
            <p>{isLoading ? 'Loading...' : currentUser?.username ?? 'Unknown'}</p>
          </div>
          <div className="stat-card">
            <strong>Role</strong>
            <p>{isLoading ? 'Loading...' : currentUser?.role ?? 'Unknown'}</p>
          </div>
          <div className="stat-card">
            <strong>Status</strong>
            <p>{isLoading ? 'Loading...' : currentUser?.status ?? 'Unknown'}</p>
          </div>
          <div className="stat-card token-preview">
            <strong>Token Preview</strong>
            <p>{tokenPreview}</p>
          </div>
        </div>
      </section>
    </AppLayout>
  )
}
