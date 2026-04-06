/**
 * Open-redirect and unsafe-navigation hardening for window.open / location.href.
 */

const GOOGLE_OAUTH_HOSTS = new Set([
  'accounts.google.com',
  'oauth2.googleapis.com',
  'www.googleapis.com',
])

function parseTrustedDownloadHostsFromEnv() {
  try {
    const raw =
      (typeof import.meta !== 'undefined' && import.meta.env?.VITE_TRUSTED_DOWNLOAD_HOSTS) || ''
    return raw
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)
  } catch {
    return []
  }
}

function isTrustedDownloadHost(hostname) {
  const h = (hostname || '').toLowerCase()
  if (!h) return false
  if (h === 'localhost' || h === '127.0.0.1' || h === '[::1]') return true
  if (h.endsWith('.amazonaws.com') || h.endsWith('.amazonaws.com.cn')) return true
  if (h.endsWith('.cloudfront.net')) return true
  for (const entry of parseTrustedDownloadHostsFromEnv()) {
    if (h === entry || h.endsWith('.' + entry)) return true
  }
  return false
}

/**
 * Google OAuth authorization URLs only (HTTPS + known Google hosts).
 */
export function assertTrustedGoogleOAuthUrl(url) {
  if (!url || typeof url !== 'string') return false
  const trimmed = url.trim()
  let u
  try {
    u = new URL(trimmed)
  } catch {
    return false
  }
  if (u.protocol !== 'https:') return false
  return GOOGLE_OAUTH_HOSTS.has(u.hostname.toLowerCase())
}

/**
 * Same allowlist as Google sign-in; Gmail integration uses the same OAuth endpoints.
 */
export function assertTrustedGmailOAuthUrl(url) {
  return assertTrustedGoogleOAuthUrl(url)
}

export function navigateTopLevelToGoogleOAuth(url) {
  if (!assertTrustedGoogleOAuthUrl(url)) {
    throw new Error('Refusing navigation to non-Google OAuth URL')
  }
  window.location.href = url.trim()
}

export function assertSafeDownloadUrl(url) {
  if (!url || typeof url !== 'string') return false
  const trimmed = url.trim()
  if (!trimmed) return false

  const lowered = trimmed.toLowerCase()
  if (
    lowered.startsWith('javascript:') ||
    lowered.startsWith('vbscript:') ||
    lowered.startsWith('data:text/html')
  ) {
    return false
  }

  if (trimmed.startsWith('/')) {
    if (trimmed.startsWith('//')) return false
    return true
  }

  if (lowered.startsWith('blob:') || lowered.startsWith('data:application/')) {
    return true
  }

  if (lowered.startsWith('https://') || lowered.startsWith('http://')) {
    try {
      const u = new URL(trimmed)
      const proto = u.protocol.toLowerCase()
      if (proto === 'http:') {
        return isTrustedDownloadHost(u.hostname)
      }
      if (proto === 'https:') {
        if (typeof window !== 'undefined' && u.origin === window.location.origin) {
          return true
        }
        return isTrustedDownloadHost(u.hostname)
      }
    } catch {
      return false
    }
  }

  return false
}

export function openUrlInNewTabSafe(url) {
  if (!assertSafeDownloadUrl(url)) return null
  return window.open(String(url).trim(), '_blank', 'noopener,noreferrer')
}

export async function openDownloadInNewTabWithAnchorFallback(url, fileName = 'download') {
  if (!assertSafeDownloadUrl(url)) return false

  const newWindow = openUrlInNewTabSafe(url)
  if (newWindow) return true

  const link = document.createElement('a')
  link.href = String(url).trim()
  link.setAttribute('download', String(fileName || 'download'))
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  return true
}
