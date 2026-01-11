// Import the centralized API configuration
import { API_BASE_URL as CONFIG_API_BASE_URL } from '@/config/api.js'

const stripTrailingSlash = (value = '') => value.replace(/\/+$/, '')

// Use the centralized API configuration
const API_BASE_URL = stripTrailingSlash(CONFIG_API_BASE_URL)

// Extract origin from base URL
const API_ORIGIN = (() => {
  try {
    const url = new URL(API_BASE_URL)
    return url.origin
  } catch {
    // Fallback: extract origin manually
    if (API_BASE_URL.startsWith('http://') || API_BASE_URL.startsWith('https://')) {
      const match = API_BASE_URL.match(/^(https?:\/\/[^/]+)/)
      return match ? match[1] : 'https://grc-tprm.vardaands.com'
    }
    return 'https://grc-tprm.vardaands.com'
  }
})()

const joinUrl = (base, path = '') => {
  const cleanBase = stripTrailingSlash(base)
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return cleanPath ? `${cleanBase}/${cleanPath}` : cleanBase
}

const API_V1_BASE_URL = joinUrl(API_BASE_URL, 'v1')

// TPRM API Base URL - use the centralized config
const TPRM_API_BASE_URL = API_BASE_URL
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
