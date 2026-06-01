import {API_BASE_URL, API_KEY} from '../lib/config';
import type {MenuItemView} from '../types/menu';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** GET /api/menu/menu — full menu (key-authed), same endpoint the POS reads. */
export async function fetchMenu(signal?: AbortSignal): Promise<MenuItemView[]> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  if (signal) signal.addEventListener('abort', () => ctrl.abort(), {once: true});

  try {
    const res = await fetch(`${API_BASE_URL}/api/menu/menu`, {
      headers: {Accept: 'application/json', 'X-API-Key': API_KEY},
      signal: ctrl.signal,
    });
    if (!res.ok) throw new ApiError('GET /api/menu/menu failed', res.status);
    return (await res.json()) as MenuItemView[];
  } finally {
    clearTimeout(timer);
  }
}
