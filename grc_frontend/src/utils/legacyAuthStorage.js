/**
 * Legacy JWT keys that must never be sent alongside HttpOnly cookie sessions.
 * Stale values here cause "Session invalidated due to newer login" when the
 * backend prefers or falls back to the Authorization header.
 */
export const LEGACY_JWT_STORAGE_KEYS = [
  'access_token',
  'refresh_token',
  'session_token',
  'token',
  'jwt_token',
  'auth_token',
]

export function clearLegacyClientJwtKeys() {
  for (const k of LEGACY_JWT_STORAGE_KEYS) {
    try {
      sessionStorage.removeItem(k)
      localStorage.removeItem(k)
    } catch {
      /* ignore */
    }
  }
}
