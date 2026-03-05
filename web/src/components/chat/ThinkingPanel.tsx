import type { StreamEvent } from '../../types/events'

interface ThinkingPanelProps {
  events: StreamEvent[]
}

export function ThinkingPanel({ events }: ThinkingPanelProps) {
  const thinking = events
    .filter((event): event is Extract<StreamEvent, { event_type: 'run.token.delta' }> =>
      event.event_type === 'run.token.delta',
    )
    .map((event) => event.payload?.delta ?? '')
    .join('')
    .trim()

  if (!thinking) {
    return null
  }

  return (
    <section className="chat-subpanel">
      <h3 className="chat-subpanel-title">Thinking</h3>
      <p className="chat-content">{thinking}</p>
    </section>
  )
}
