import { ChatPanel } from '../components/chat/ChatPanel'
import { AppLayout } from '../components/layout/AppLayout'
import { useHealthQuery } from '../hooks/useApi'

export function Chat() {
  const { data, isLoading, isError } = useHealthQuery()

  return (
    <AppLayout title="Portex Chat">
      <section className="panel" style={{ marginBottom: '1rem' }}>
        <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Runtime Status</h2>
        {isLoading ? <span className="muted">Checking backend...</span> : null}
        {isError ? <span className="error-text">Backend is currently unreachable.</span> : null}
        {!isLoading && !isError && data ? (
          <span className="status-badge">
            {data.status} · v{data.version}
          </span>
        ) : null}
      </section>
      <ChatPanel />
    </AppLayout>
  )
}
