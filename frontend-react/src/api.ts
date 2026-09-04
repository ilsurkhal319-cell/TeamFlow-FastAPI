export const API = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

function handleUnauthorized(path: string, status: number) {
  if (status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/register')) {
    localStorage.removeItem('teamflow_token');
    if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) window.location.replace('/login/');
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('teamflow_token');
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
  if (!response.ok) { handleUnauthorized(path, response.status); const body = await response.json().catch(() => ({})); throw new ApiError(response.status === 401 ? 'Сессия истекла. Войдите снова.' : body.detail || 'Request failed', response.status); }
  return (response.status === 204 ? null : response.json()) as Promise<T>;
}
