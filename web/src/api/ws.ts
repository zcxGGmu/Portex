export type WebSocketMessage =
  | string
  | number
  | boolean
  | null
  | WebSocketMessage[]
  | { [key: string]: WebSocketMessage }

export type WebSocketMessageHandler = (
  message: WebSocketMessage,
  event: MessageEvent,
) => void

export interface CreateWebSocketOptions {
  baseUrl?: string
  protocols?: string | string[]
}

const DEFAULT_WS_BASE_URL = 'ws://localhost:8000'

function toWsBaseUrl(value: string): string {
  if (value.startsWith('ws://') || value.startsWith('wss://')) {
    return value
  }

  if (value.startsWith('http://')) {
    return `ws://${value.slice('http://'.length)}`
  }

  if (value.startsWith('https://')) {
    return `wss://${value.slice('https://'.length)}`
  }

  return value
}

function resolveWsBaseUrl(override?: string): string {
  if (override) {
    return toWsBaseUrl(override)
  }

  const configuredWsBase = import.meta.env.VITE_WS_BASE_URL as string | undefined
  if (configuredWsBase) {
    return toWsBaseUrl(configuredWsBase)
  }

  const configuredApiBase = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (configuredApiBase) {
    return toWsBaseUrl(configuredApiBase)
  }

  if (typeof window !== 'undefined' && window.location?.host) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}`
  }

  return DEFAULT_WS_BASE_URL
}

export function resolveWebSocketUrl(
  groupFolder: string,
  options: Pick<CreateWebSocketOptions, 'baseUrl'> = {},
): string {
  const encodedGroupFolder = encodeURIComponent(groupFolder)
  const baseUrl = resolveWsBaseUrl(options.baseUrl).replace(/\/+$/, '')
  return `${baseUrl}/ws/${encodedGroupFolder}`
}

export function parseWebSocketMessage(rawData: unknown): WebSocketMessage {
  if (typeof rawData !== 'string') {
    return (rawData ?? null) as WebSocketMessage
  }

  try {
    return JSON.parse(rawData) as WebSocketMessage
  } catch {
    return rawData
  }
}

export function subscribeWebSocketMessages(
  websocket: WebSocket,
  handler: WebSocketMessageHandler,
): () => void {
  const listener = (event: MessageEvent) => {
    handler(parseWebSocketMessage(event.data), event)
  }

  websocket.addEventListener('message', listener)
  return () => websocket.removeEventListener('message', listener)
}

export function createWebSocket(
  groupFolder: string,
  options: CreateWebSocketOptions = {},
): WebSocket {
  return new WebSocket(resolveWebSocketUrl(groupFolder, options), options.protocols)
}
