export type StreamEvent =
  | { event_type: 'run.started'; run_id: string; payload?: Record<string, unknown> }
  | { event_type: 'run.token.delta'; run_id: string; payload: { delta?: string } }
  | {
      event_type: 'run.tool.started'
      run_id: string
      payload: { tool_name?: string; tool_call_id?: string }
    }
  | {
      event_type: 'run.tool.completed'
      run_id: string
      payload: { tool_name?: string; tool_call_id?: string; output?: unknown }
    }
  | { event_type: 'run.timeout'; run_id: string; payload?: { status?: string; timeout_ms?: number } }
  | { event_type: 'run.completed'; run_id: string; payload?: { final_output?: string } }
  | { event_type: 'run.failed'; run_id: string; payload?: { error?: string; status?: string } }

const STREAM_EVENT_TYPES: StreamEvent['event_type'][] = [
  'run.started',
  'run.token.delta',
  'run.tool.started',
  'run.tool.completed',
  'run.timeout',
  'run.completed',
  'run.failed',
]

export function isStreamEvent(value: unknown): value is StreamEvent {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const candidate = value as { event_type?: unknown; run_id?: unknown }
  if (typeof candidate.event_type !== 'string' || typeof candidate.run_id !== 'string') {
    return false
  }

  return STREAM_EVENT_TYPES.includes(candidate.event_type as StreamEvent['event_type'])
}
