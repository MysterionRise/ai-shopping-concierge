const API_BASE = '/api/v1'

/** Currently active user ID, set by setActiveUserId(). Sent as X-User-ID header. */
let _activeUserId: string | null = null

export function setActiveUserId(userId: string | null): void {
  _activeUserId = userId
}

export function getActiveUserId(): string | null {
  return _activeUserId
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (_activeUserId) {
    headers['X-User-ID'] = _activeUserId
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export function apiStreamUrl(path: string): string {
  return `${API_BASE}${path}`
}
