/**
 * Config from Vite env vars (see `.env.example`). Same keys/convention as the
 * POS and the kitchen board so every Pi provisions the same way.
 *
 *   VITE_API_BASE_URL  e.g. http://192.168.1.50:8080
 *   VITE_API_KEY       must match the server's app.api-key
 *   VITE_POLL_MS       menu refresh interval (default 30000 — menus change
 *                      far less often than orders, mostly via 86'ing)
 *   VITE_BOARD_TITLE   optional heading text (default "Menu")
 */
export const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080'
).replace(/\/+$/, '');

export const API_KEY: string = import.meta.env.VITE_API_KEY ?? '';

export const POLL_MS: number = Number(import.meta.env.VITE_POLL_MS ?? 30000);

export const BOARD_TITLE: string = import.meta.env.VITE_BOARD_TITLE ?? 'Menu';

if (!API_KEY) {
  // eslint-disable-next-line no-console
  console.warn('[config] VITE_API_KEY is empty — /api/menu/menu will 401.');
}