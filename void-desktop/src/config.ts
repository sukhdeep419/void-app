const DEFAULT_API_BASE = 'http://localhost:8000'

export function getApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_VOID_API_URL as string | undefined
  const base = fromEnv?.trim() || DEFAULT_API_BASE
  return base.replace(/\/$/, '')
}

export function getSystemWebSocketUrl(): string {
  const base = getApiBaseUrl()
  const wsBase = base.replace(/^http/, 'ws')
  return `${wsBase}/ws/system`
}

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getApiBaseUrl()}${normalizedPath}`
}
