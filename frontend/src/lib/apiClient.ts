/**
 * Centralized API client for FraudSense AI
 *
 * In development:  Vite proxy forwards /api/* to localhost:8000 (stripping /api prefix)
 * In production:   Vercel rewrites /api/* to the Render backend URL (preserving /api prefix)
 *
 * The `VITE_API_URL` env var can override the base for custom deployments.
 * Leave it unset to use the relative `/api` path (works with both Vite proxy and Vercel rewrites).
 */

const VITE_API_URL = import.meta.env.VITE_API_URL as string | undefined;

/**
 * Resolve the correct base URL for API calls.
 *
 * - If VITE_API_URL is set (e.g. "https://fraudsense-api.onrender.com"), use it directly.
 * - Otherwise fall back to the relative path "/api" which is handled by:
 *     - Vite dev proxy  → strips /api and forwards to localhost:8000
 *     - Vercel rewrites → proxies to the Render backend (see vercel.json)
 */
export function getApiBase(): string {
  if (VITE_API_URL) {
    return VITE_API_URL.replace(/\/$/, ''); // strip trailing slash
  }
  return '/api';
}

export const API_BASE = getApiBase();

/**
 * Thin wrapper around fetch that:
 *  - Prepends the correct base URL
 *  - Sets Content-Type: application/json for POST/PATCH/PUT bodies
 *  - Throws a descriptive error on non-OK responses
 */
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string>),
  };

  // Auto-set Content-Type for JSON bodies
  if (init?.body && typeof init.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, { ...init, headers });
  return response;
}
