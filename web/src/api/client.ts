export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CurrentUser {
  id: string
  username: string
  role: string
  status: string
}

export interface HealthResponse {
  status: string
  version: string
}

interface RequestOptions extends RequestInit {
  token?: string | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  details: unknown

  constructor(message: string, status: number, details: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...restOptions } = options
  const resolvedHeaders = new Headers(headers)

  if (!resolvedHeaders.has('Content-Type')) {
    resolvedHeaders.set('Content-Type', 'application/json')
  }

  if (token) {
    resolvedHeaders.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...restOptions,
    headers: resolvedHeaders,
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type')
    const details = contentType?.includes('application/json')
      ? await response.json()
      : await response.text()

    const detailMessage =
      typeof details === 'object' &&
      details !== null &&
      'detail' in details &&
      typeof (details as { detail: unknown }).detail === 'string'
        ? (details as { detail: string }).detail
        : `Request failed with status ${response.status}`

    throw new ApiError(detailMessage, response.status, details)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const apiClient = {
  login(username: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },
  getCurrentUser(token: string): Promise<CurrentUser> {
    return request<CurrentUser>('/users/me', { token })
  },
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health')
  },
}
