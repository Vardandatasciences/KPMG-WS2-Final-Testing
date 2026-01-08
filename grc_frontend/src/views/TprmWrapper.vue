<template>
  <div class="tprm-wrapper">
    <div v-if="!hasBaseUrl" class="tprm-wrapper__message">
      <p>
        <strong>VUE_APP_TPRM_BASE_URL</strong> is not configured. Set it in your
        <code>.env</code> file to embed the TPRM application.
      </p>
    </div>
    <div v-else class="tprm-wrapper__frame">
      <iframe
        ref="tprmIframe"
        :src="iframeSrc"
        :key="iframeKey"
        title="TPRM Module"
        frameborder="0"
        referrerpolicy="no-referrer"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads allow-popups-to-escape-sandbox"
        @load="onIframeLoad"
        @error="onIframeError"
      />
    </div>
  </div>
</template>

<script>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Get TPRM base URL from env or use fallback based on current location
const getTprmBaseUrl = () => {
  // Debug logging to see what's happening
  const debugInfo = {
    hasEnvVar: !!process.env.VUE_APP_TPRM_BASE_URL,
    envVarValue: process.env.VUE_APP_TPRM_BASE_URL,
    nodeEnv: process.env.NODE_ENV,
    hostname: typeof window !== 'undefined' ? window.location?.hostname : 'unknown',
    href: typeof window !== 'undefined' ? window.location?.href : 'unknown'
  }
  
  // Check if we're on production domain FIRST
  const isProductionDomain = typeof window !== 'undefined' && window.location && 
    (window.location.hostname.includes('vardaands.com') || 
     window.location.hostname.includes('grc-tprm') ||
     window.location.href.includes('vardaands.com'))
  
  // First, check Vue CLI-style environment variable (highest priority)
  // BUT: Ignore localhost values if we're on production domain
  if (process.env.VUE_APP_TPRM_BASE_URL) {
    const envUrl = process.env.VUE_APP_TPRM_BASE_URL
    
    // CRITICAL: If env var is localhost but we're on production domain, IGNORE IT
    if (isProductionDomain && (envUrl.includes('localhost') || envUrl.includes('127.0.0.1'))) {
      console.warn('[TprmWrapper] ⚠️ VUE_APP_TPRM_BASE_URL is set to localhost but running on production domain!')
      console.warn('[TprmWrapper] Ignoring env var and using production URL instead')
      console.warn('[TprmWrapper] Fix: Remove or update VUE_APP_TPRM_BASE_URL in your .env file')
      // Fall through to use production URL
    } else {
      console.log('[TprmWrapper] Using VUE_APP_TPRM_BASE_URL:', envUrl, debugInfo)
      return envUrl
    }
  }

  // CRITICAL: TPRM should be served from the same origin as GRC at /tprm subdirectory
  // This prevents CORS issues and ensures proper routing
  if (typeof window !== 'undefined' && window.location) {
    const origin = window.location.origin
    const hostname = window.location.hostname
    
    // Production: use same origin with /tprm prefix
    if (hostname.includes('vardaands.com') || hostname.includes('grc-tprm')) {
      const tprmBaseUrl = `${origin}/tprm`
      console.log('[TprmWrapper] Production domain detected, using same origin with /tprm:', tprmBaseUrl, debugInfo)
      return tprmBaseUrl
    }
    
    // Development: use localhost:3000 (TPRM dev server)
    if ((hostname === 'localhost' || hostname === '127.0.0.1') && 
        process.env.NODE_ENV === 'development') {
      console.log('[TprmWrapper] Development mode on localhost, using localhost:3000', debugInfo)
      return `http://${hostname}:3000`
    }
    
    // Any other domain: use same origin with /tprm prefix
    const tprmBaseUrl = `${origin}/tprm`
    console.log('[TprmWrapper] Using same origin with /tprm prefix:', tprmBaseUrl, debugInfo)
    return tprmBaseUrl
  }

  // Fallback: use same origin with /tprm
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.origin}/tprm`
  }
  
  console.log('[TprmWrapper] Using default fallback /tprm', debugInfo)
  return '/tprm'
}

// Don't call at module level - call in setup() for runtime evaluation
// const BASE_URL = getTprmBaseUrl() // REMOVED - will be computed in setup()

export default {
  name: 'TprmWrapper',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const tprmIframe = ref(null)
    
    // Call at runtime, not module load time
    const BASE_URL = getTprmBaseUrl()

    const normalizedPath = computed(() => {
      const param = route.params.tprmPath

      let pathValue = ''
      if (Array.isArray(param)) {
        pathValue = param.join('/')
      } else if (typeof param === 'string') {
        pathValue = param
      }

      // If no path value, default to '/' (home page)
      // But ensure it's a valid path for the TPRM app
      const cleanPath = pathValue ? `/${pathValue}` : '/'
      
      // Remove any leading/trailing slashes and ensure single leading slash
      let normalized = cleanPath.replace(/^\/+|\/+$/g, '')
      normalized = normalized ? `/${normalized}` : '/'
      
      const query = route.query
      const queryString = new URLSearchParams(query).toString()

      return queryString ? `${normalized}?${queryString}` : normalized
    })

    // Track the last path we navigated to, to prevent duplicate navigations
    const lastNavigatedPath = ref(null)
    
    // Track if iframe has been loaded at least once
    const iframeLoaded = ref(false)
    
    // CRITICAL FIX: Store initial src and don't change it after iframe loads
    // This prevents the iframe from reloading on every route change
    const initialPath = ref(normalizedPath.value)
    const iframeSrc = computed(() => {
      if (!BASE_URL) return ''
      const base = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL
      // Only use initial path if iframe hasn't loaded yet
      // After it loads, keep the src static and navigate via postMessage
      const pathToUse = iframeLoaded.value ? initialPath.value : normalizedPath.value
      return `${base}${pathToUse}`
    })
    
    // Use a key that only changes when we actually need to reload the iframe
    // This prevents Vue from recreating the iframe on every route change
    const iframeKey = computed(() => {
      // Only change key if base URL changes (shouldn't happen in production)
      return BASE_URL ? BASE_URL : 'default'
    })

    // Get auth data from GRC localStorage
    const getAuthData = () => {
      const token = localStorage.getItem('access_token') || 
                    localStorage.getItem('session_token') || 
                    localStorage.getItem('token')
      const user = localStorage.getItem('user') || localStorage.getItem('current_user')
      const refreshToken = localStorage.getItem('refresh_token')
      
      return {
        type: 'GRC_AUTH_SYNC',
        token,
        refreshToken,
        user: user ? JSON.parse(user) : null,
        isAuthenticated: localStorage.getItem('isAuthenticated') === 'true' || 
                         localStorage.getItem('is_logged_in') === 'true'
      }
    }

    // Send auth data to TPRM iframe
    const sendAuthToIframe = () => {
      if (tprmIframe.value && tprmIframe.value.contentWindow) {
        const authData = getAuthData()
        console.log('[TprmWrapper] Sending auth data to TPRM iframe:', { 
          hasToken: !!authData.token, 
          hasUser: !!authData.user,
          isAuthenticated: authData.isAuthenticated 
        })
        tprmIframe.value.contentWindow.postMessage(authData, '*')
      }
    }

    const onIframeLoad = () => {
      console.log('[TprmWrapper] TPRM iframe loaded, syncing auth...')
      console.log('[TprmWrapper] Iframe src:', iframeSrc.value)
      console.log('[TprmWrapper] Current route path:', route.path)
      console.log('[TprmWrapper] Normalized path:', normalizedPath.value)
      
      // Mark iframe as loaded - this prevents src from changing on route changes
      iframeLoaded.value = true
      // Store the initial path so we can keep src static
      initialPath.value = normalizedPath.value
      lastNavigatedPath.value = normalizedPath.value
      
      // Small delay to ensure iframe is ready to receive messages
      setTimeout(() => {
        sendAuthToIframe()
        
        // Request current route from iframe after it loads
        if (tprmIframe.value && tprmIframe.value.contentWindow) {
          // Ask iframe for its current route
          tprmIframe.value.contentWindow.postMessage({ type: 'GET_CURRENT_ROUTE' }, '*')
          
          // The iframe should already be at the correct route from the URL
          // Router will read it from window.location.pathname
          // If it's not at the right route, navigate it
          const targetPath = normalizedPath.value
          if (targetPath && targetPath !== '/') {
            setTimeout(() => {
              if (tprmIframe.value && tprmIframe.value.contentWindow) {
                tprmIframe.value.contentWindow.postMessage({ 
                  type: 'NAVIGATE_TO_ROUTE', 
                  path: targetPath 
                }, '*')
              }
            }, 500)
          }
        }
        
        // Retry after 1 second in case first attempt failed
        setTimeout(sendAuthToIframe, 1000)
      }, 100)
    }
    
    // Watch for route changes and navigate iframe without reloading
    // CRITICAL: Only navigate via postMessage if iframe is already loaded
    // This prevents reloading the iframe on every route change
    watch(() => normalizedPath.value, (newPath, oldPath) => {
      // Only navigate if:
      // 1. Path actually changed
      // 2. Iframe is loaded (not initial load)
      // 3. Path is different from last navigated path
      // 4. Iframe ref exists
      if (iframeLoaded.value && 
          newPath !== oldPath && 
          tprmIframe.value && 
          tprmIframe.value.contentWindow && 
          newPath !== lastNavigatedPath.value) {
        console.log('[TprmWrapper] Route changed, navigating iframe via postMessage (no reload):', newPath)
        tprmIframe.value.contentWindow.postMessage({ 
          type: 'NAVIGATE_TO_ROUTE', 
          path: newPath 
        }, '*')
        lastNavigatedPath.value = newPath
      }
    })
    
    // Handle iframe errors
    const onIframeError = (error) => {
      console.error('[TprmWrapper] Iframe error:', error)
      console.error('[TprmWrapper] Failed to load TPRM from:', iframeSrc.value)
      console.error('[TprmWrapper] Check that VUE_APP_TPRM_BASE_URL is configured correctly')
    }

    // Listen for messages from TPRM iframe (auth requests and navigation)
    const handleMessage = (event) => {
      // Verify origin if BASE_URL is configured
      if (BASE_URL) {
        const baseOrigin = new URL(BASE_URL).origin
        if (event.origin !== baseOrigin && event.origin !== window.location.origin) {
          return
        }
      }

      if (event.data && event.data.type === 'TPRM_AUTH_REQUEST') {
        console.log('[TprmWrapper] Received auth request from TPRM')
        sendAuthToIframe()
      }
      
      // Handle redirect request from TPRM iframe (when authentication is required)
      if (event.data && event.data.type === 'TPRM_REDIRECT_TO_LOGIN') {
        console.log('[TprmWrapper] Received redirect to login request from TPRM iframe')
        // Redirect parent window to GRC login
        window.location.href = '/login'
      }
      
      // Helper function to normalize TPRM path and convert to parent route
      const normalizeTprmPath = (tprmPath) => {
        if (!tprmPath) return '/tprm'
        
        // Remove /tprm/ prefix if present (defensive - shouldn't happen but prevents loops)
        let normalized = tprmPath.replace(/^\/tprm\/?/, '/')
        
        // Ensure it starts with /
        if (!normalized.startsWith('/')) {
          normalized = '/' + normalized
        }
        
        // Convert to parent route format
        return normalized === '/' ? '/tprm' : `/tprm${normalized}`
      }
      
      // Handle navigation sync from TPRM iframe
      if (event.data && event.data.type === 'TPRM_NAVIGATION') {
        const tprmPath = event.data.path || ''
        const newPath = normalizeTprmPath(tprmPath)
        console.log('[TprmWrapper] Received navigation from TPRM iframe:', tprmPath, '-> Updating parent route to:', newPath)
        
        // Update parent router using replace to avoid adding to history stack
        // This prevents navigation loops and multiple page loads
        // Only update if the path is actually different
        if (route.path !== newPath && !route.path.startsWith(newPath + '/')) {
          router.replace(newPath).catch(err => {
            // Ignore navigation errors (e.g., if already on that route)
            if (err.name !== 'NavigationDuplicated' && !err.message?.includes('already being navigated')) {
              console.warn('[TprmWrapper] Navigation error:', err)
            }
          })
        }
      }
      
      // Handle route request from iframe (when iframe loads)
      if (event.data && event.data.type === 'CURRENT_ROUTE') {
        const tprmPath = event.data.path || ''
        const newPath = normalizeTprmPath(tprmPath)
        console.log('[TprmWrapper] Received current route from TPRM iframe:', tprmPath, '-> Syncing parent route to:', newPath)
        
        // Only update if we're not already on the correct route
        // Use replace to avoid adding to history stack
        // Check if current path matches or is a sub-path of the target
        if (route.path !== newPath && !route.path.startsWith(newPath + '/')) {
          router.replace(newPath).catch(err => {
            // Ignore navigation duplicates and already-matched routes
            if (err.name !== 'NavigationDuplicated' && !err.message?.includes('already being navigated')) {
              console.warn('[TprmWrapper] Route sync error:', err)
            }
          })
        }
      }
    }

    // Set up message listener and log configuration on mount
    onMounted(() => {
      window.addEventListener('message', handleMessage)
      console.log('[TprmWrapper] ========== DEBUG INFO ==========')
      console.log('[TprmWrapper] BASE_URL:', BASE_URL)
      console.log('[TprmWrapper] NODE_ENV:', process.env.NODE_ENV)
      console.log('[TprmWrapper] VUE_APP_TPRM_BASE_URL:', process.env.VUE_APP_TPRM_BASE_URL)
      console.log('[TprmWrapper] window.location.hostname:', window.location?.hostname)
      console.log('[TprmWrapper] window.location.href:', window.location?.href)
      console.log('[TprmWrapper] Current route:', route.path)
      console.log('[TprmWrapper] Iframe will load:', iframeSrc.value)
      console.log('[TprmWrapper] =================================')
      if (!BASE_URL) {
        console.warn('[TprmWrapper] WARNING: VUE_APP_TPRM_BASE_URL is not configured!')
        console.warn('[TprmWrapper] TPRM pages will not load. Set VUE_APP_TPRM_BASE_URL in .env file')
      }
      // Only warn about localhost in production, not in development
      if (BASE_URL.includes('localhost') && process.env.NODE_ENV === 'production') {
        console.error('[TprmWrapper] ⚠️⚠️⚠️ ERROR: Using localhost URL in production!')
        console.error('[TprmWrapper] This will cause CORS errors. Check environment variables.')
      } else if (BASE_URL.includes('localhost') && process.env.NODE_ENV === 'development') {
        console.log('[TprmWrapper] ✓ Using localhost URL in development mode (expected)')
      }
    })

    onUnmounted(() => {
      window.removeEventListener('message', handleMessage)
    })

    return {
      tprmIframe,
      iframeSrc,
      iframeKey,
      hasBaseUrl: computed(() => Boolean(BASE_URL)),
      onIframeLoad,
      onIframeError
    }
  }
}
</script>

<style scoped>
.tprm-wrapper {
  width: 100%;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  background: #f5f6fb;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e3e7f0;
}

.tprm-wrapper__frame {
  flex: 1;
  position: relative;
}

.tprm-wrapper__frame iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
  background: white;
}

.tprm-wrapper__message {
  padding: 32px;
  text-align: center;
  color: #0f172a;
}

.tprm-wrapper__message code {
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}
</style>

