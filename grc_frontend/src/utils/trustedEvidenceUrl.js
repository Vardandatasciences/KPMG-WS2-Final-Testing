export function isTrustedEvidenceUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== 'string') return false;
  const url = rawUrl.trim();
  if (!url) return false;

  // Internal placeholders (never fetched)
  if (url.startsWith('#linked-event-')) return true;

  // Relative URLs (served by this origin)
  if (url.startsWith('/')) return true;

  let parsed;
  try {
    parsed = new URL(url, window.location.origin);
  } catch {
    return false;
  }

  const scheme = (parsed.protocol || '').toLowerCase();
  const host = (parsed.hostname || '').toLowerCase();

  // Evidence should be HTTPS in real deployments.
  if (scheme !== 'https:' && scheme !== 'http:') return false;

  const allowHosts = new Set([
    window.location.hostname.toLowerCase(),
    'riskavaire.vardaands.com',
    'test-riskavaire.vardaands.com',
    'grc-tprm.vardaands.com',
  ]);

  const allowSuffixes = ['amazonaws.com', 'cloudfront.net'];

  if (allowHosts.has(host)) {
    // Allow http only for localhost-style dev
    if (scheme === 'http:' && host !== 'localhost' && host !== '127.0.0.1') return false;
    return true;
  }

  return allowSuffixes.some((s) => host === s || host.endsWith(`.${s}`));
}

export function safeEvidenceUrl(rawUrl) {
  return isTrustedEvidenceUrl(rawUrl) ? rawUrl : null;
}
