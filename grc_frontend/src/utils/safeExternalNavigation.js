export function assertSafeDownloadUrl(url) {
  if (!url || typeof url !== 'string') return false
  const trimmed = url.trim()
  if (!trimmed) return false

  const lowered = trimmed.toLowerCase()
  // Block scriptable/unsafe schemes.
  if (
    lowered.startsWith('javascript:') ||
    lowered.startsWith('vbscript:') ||
    lowered.startsWith('data:text/html')
  ) {
    return false
  }

  // Allow relative URLs and typical absolute URLs used by downloads.
  if (
    trimmed.startsWith('/') ||
    lowered.startsWith('http://') ||
    lowered.startsWith('https://') ||
    lowered.startsWith('blob:') ||
    lowered.startsWith('data:application/')
  ) {
    return true
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

  // Popup blocked: fallback to anchor click.
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

