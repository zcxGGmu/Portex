import type { StreamEvent } from '../../types/events'

interface ToolCallTrackerProps {
  events: StreamEvent[]
}

export function ToolCallTracker({ events }: ToolCallTrackerProps) {
  const toolEvents = events.filter(
    (
      event,
    ): event is
      | Extract<StreamEvent, { event_type: 'run.tool.started' }>
      | Extract<StreamEvent, { event_type: 'run.tool.completed' }> =>
      event.event_type === 'run.tool.started' || event.event_type === 'run.tool.completed',
  )

  if (toolEvents.length === 0) {
    return null
  }

  return (
    <section className="chat-subpanel">
      <h3 className="chat-subpanel-title">Tool Calls</h3>
      <ul className="tool-call-list">
        {toolEvents.map((event, index) => {
          const toolName = event.payload.tool_name ?? 'unknown_tool'
          const status = event.event_type === 'run.tool.started' ? 'started' : 'completed'
          return (
            <li className="tool-call-item" key={`${event.run_id}-${event.event_type}-${index}`}>
              <span>{toolName}</span>
              <span className="muted">{status}</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
