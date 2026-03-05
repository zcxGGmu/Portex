export type WebSocketEventPayload = unknown

export type ParsedWebSocketMessage =
  | {
      kind: 'json'
      raw: string
      data: WebSocketEventPayload
    }
  | {
      kind: 'text'
      raw: string
      data: string
    }

export interface WebSocketMessageEnvelope {
  event: MessageEvent<string>
  message: ParsedWebSocketMessage
}

export interface CreateWebSocketOptions {
  baseUrl?: string
  protocols?: string | string[]
}

function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, '')
}

function resolveBaseUrl(override?: string): string {
  if (override) {
    return trimTrailingSlashes(override)
  }

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}`
  }

  return 'ws://localhost:8000'
}

function parseMessageData(raw: string): ParsedWebSocketMessage {
  try {
    return {
      kind: 'json',
      raw,
      data: JSON.parse(raw) as WebSocketEventPayload,
    }
  } catch {
    return {
      kind: 'text',
      raw,
      data: raw,
    }
  }
}

export function createWebSocket(
  groupFolder: string,
  options: CreateWebSocketOptions = {},
): WebSocket {
  const encodedGroup = encodeURIComponent(groupFolder)
  const baseUrl = resolveBaseUrl(options.baseUrl)
  const url = `${baseUrl}/ws/${encodedGroup}`

  return new WebSocket(url, options.protocols)
}

export function subscribeWebSocketMessages(
  socket: WebSocket,
  onMessage: (envelope: WebSocketMessageEnvelope) => void,
): () => void {
  const handler = (event: MessageEvent<string>) => {
    const raw = typeof event.data === 'string' ? event.data : String(event.data)
    onMessage({
      event,
      message: parseMessageData(raw),
    })
  }

  socket.addEventListener('message', handler as EventListener)
  return () => {
    socket.removeEventListener('message', handler as EventListener)
  }
}

