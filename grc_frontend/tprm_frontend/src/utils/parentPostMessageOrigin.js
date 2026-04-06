/**
 * Target origin for postMessage from TPRM (iframe) → GRC parent.
 * Never use '*'. Set VITE_PARENT_APP_ORIGIN in production if referrer/ancestorOrigins are unavailable.
 */
export function getParentPostMessageTargetOrigin() {
  const envRaw =
    typeof import.meta !== 'undefined' && import.meta.env?.VITE_PARENT_APP_ORIGIN
      ? String(import.meta.env.VITE_PARENT_APP_ORIGIN).trim()
      : ''
  if (envRaw) {
    try {
      return new URL(envRaw).origin
    } catch {
      /* fall through */
    }
  }
  try {
    if (typeof document !== 'undefined' && document.referrer) {
      return new URL(document.referrer).origin
    }
  } catch {
    /* ignore */
  }
  try {
    const ao = typeof window !== 'undefined' && window.location?.ancestorOrigins
    if (ao && ao.length) {
      return ao[0]
    }
  } catch {
    /* ignore */
  }
  if (typeof window !== 'undefined' && window.parent === window) {
    return window.location.origin
  }
  if (typeof window !== 'undefined') {
    return window.location.origin
  }
  return ''
}
