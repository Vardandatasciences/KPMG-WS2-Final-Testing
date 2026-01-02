const stripTrailingSlash = (value = '') => value.replace(/\/+$/, '')
const ensureLeadingSlash = (path = '') => (path.startsWith('/') ? path : `/${path}`)

const resolveWindowOrigin = () => {
  // Always check environment variables first - these take highest priority
  const envUrl = import.meta.env.VITE_API_BASE_URL?.replace('/api/tprm', '').replace('/api', '') || 
                 import.meta.env.VITE_BACKEND_URL
  
  if (envUrl) {
    // Extract origin from env URL if it's a full URL
    try {
      const url = new URL(envUrl)
      return url.origin
    } catch {
      // If it's not a full URL, return as is (will be handled by caller)
      return envUrl
    }
  }
  
  // If no environment variable, ALWAYS default to production
  // Only use localhost if explicitly set via VITE_USE_LOCALHOST=true
  if (import.meta.env.VITE_USE_LOCALHOST === 'true') {
    if (typeof window !== 'undefined' && window.location) {
      const { protocol, hostname, port } = window.location
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        const devPorts = new Set(['3000', '4173', '4174', '5173', '5174'])
        const backendPort = !port || devPorts.has(port) ? '8000' : port
        const portSegment = backendPort ? `:${backendPort}` : ''
        return `${protocol}//${hostname}${portSegment}`
      }
    }
  }
  
  // DEFAULT: Always use production URL
  return 'https://grc-tprm.vardaands.com'
}

const resolveApiBaseUrl = () => {
  const candidates = [
    import.meta.env?.VITE_API_BASE_URL,
    import.meta.env?.VITE_API_URL,
    import.meta.env?.VITE_BACKEND_URL,
    import.meta.env?.VUE_APP_API_BASE_URL,
    import.meta.env?.VUE_APP_API_URL
  ].filter(Boolean)

  if (candidates.length > 0) {
    return stripTrailingSlash(candidates[0])
  }

  // Default to production API URL
  const origin = resolveWindowOrigin()
  // If origin already includes /api, don't add it again
  if (origin.includes('/api')) {
    return stripTrailingSlash(origin)
  }
  return `${origin}/api`
}

const joinUrl = (base, path = '') => {
  const cleanBase = stripTrailingSlash(base)
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return cleanPath ? `${cleanBase}/${cleanPath}` : cleanBase
}

const API_BASE_URL = resolveApiBaseUrl()
const API_ORIGIN = (() => {
  try {
    return new URL(API_BASE_URL).origin
  } catch {
    return resolveWindowOrigin()
  }
})()
const API_V1_BASE_URL = joinUrl(API_BASE_URL, 'v1')

const resolveTprmBaseUrl = () => {
  const explicitBase = import.meta.env?.VITE_TPRM_API_BASE_URL
  if (explicitBase) {
    return stripTrailingSlash(explicitBase)
  }

  const prefix = import.meta.env?.VITE_TPRM_API_PREFIX
  if (prefix) {
    if (prefix.startsWith('http://') || prefix.startsWith('https://')) {
      return stripTrailingSlash(prefix)
    }
    return `${API_ORIGIN}${ensureLeadingSlash(stripTrailingSlash(prefix))}`
  }

  // Default to production TPRM API URL
  // If API_BASE_URL already includes /tprm, return it as is
  if (API_BASE_URL.includes('/tprm')) {
    return stripTrailingSlash(API_BASE_URL)
  }
  
  // Otherwise, append /tprm
  return joinUrl(API_BASE_URL, 'tprm')
}

const TPRM_API_BASE_URL = resolveTprmBaseUrl()
const TPRM_API_V1_BASE_URL = joinUrl(TPRM_API_BASE_URL, 'v1')

export const getApiOrigin = () => API_ORIGIN
export const getApiBaseUrl = () => API_BASE_URL
export const getApiV1BaseUrl = () => API_V1_BASE_URL
export const getTprmApiBaseUrl = () => TPRM_API_BASE_URL
export const getTprmApiV1BaseUrl = () => TPRM_API_V1_BASE_URL

export const getApiUrl = (path = '') => joinUrl(API_BASE_URL, path)
export const getApiV1Url = (path = '') => joinUrl(API_V1_BASE_URL, path)
export const getTprmApiUrl = (path = '') => joinUrl(TPRM_API_BASE_URL, path)
export const getTprmApiV1Url = (path = '') => joinUrl(TPRM_API_V1_BASE_URL, path)

