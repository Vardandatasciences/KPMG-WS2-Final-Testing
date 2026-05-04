/**
 * Session-scoped framework context (client session isolation; finding 13).
 * Do not persist framework_id to localStorage from here — logout clears legacy keys in authService.
 *
 * Default: VITE_DEFAULT_FRAMEWORK_ID env, else "1" (server should still validate).
 */
export function getDefaultFrameworkId() {
  try {
    const env = typeof import.meta !== 'undefined' && import.meta.env?.VITE_DEFAULT_FRAMEWORK_ID
    if (env != null && String(env).trim() !== '') {
      return String(env).trim()
    }
  } catch {
    /* ignore */
  }
  return '1'
}

export function getSessionFrameworkId() {
  const a = sessionStorage.getItem('framework_id')
  const b = sessionStorage.getItem('selectedFrameworkId')
  return (a && String(a).trim()) || (b && String(b).trim()) || null
}

export function getLegacyStoredFrameworkId() {
  try {
    const candidates = [
      sessionStorage.getItem('frameworkId'),
      localStorage.getItem('selectedFrameworkId'),
      localStorage.getItem('frameworkId')
    ]

    for (const value of candidates) {
      const normalized = value == null ? '' : String(value).trim()
      if (!normalized || normalized === 'null' || normalized === 'undefined' || normalized === 'all') {
        continue
      }
      return normalized
    }
  } catch {
    /* ignore storage access errors */
  }

  return null
}

export function getExplicitFrameworkId() {
  return getSessionFrameworkId() || getLegacyStoredFrameworkId() || null
}

export function setSessionFrameworkId(frameworkId) {
  if (frameworkId == null || frameworkId === '') return
  sessionStorage.setItem('framework_id', String(frameworkId))
}

/**
 * Framework id for API payloads.
 *
 * IMPORTANT:
 * Do not silently fall back to hardcoded/default framework ids here.
 * That causes UI/API flicker where pages first load framework "1" (often NIST)
 * and then jump to the actual selected framework once session state hydrates.
 */
export function getFrameworkIdForClient() {
  return getSessionFrameworkId() || getLegacyStoredFrameworkId() || null
}
