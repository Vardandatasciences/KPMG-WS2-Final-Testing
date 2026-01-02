/**
 * RFP Mobile Detection Composable
 * Secure mobile device detection with responsive utilities
 */

import { ref, onMounted, onUnmounted, computed, readonly } from 'vue'

// Mobile detection configuration
const mobileBreakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
}

// User agent patterns for mobile detection
const mobileUserAgentPatterns = [
  /Android/i,
  /webOS/i,
  /iPhone/i,
  /iPad/i,
  /iPod/i,
  /BlackBerry/i,
  /Windows Phone/i,
  /Mobile/i
]

// Touch device detection
const touchDevicePatterns = [
  /Touch/i,
  /Mobile/i,
  /Android/i,
  /iPhone/i,
  /iPad/i
]

const rfpUseIsMobile = () => {
  // Reactive state
  const windowWidth = ref(0)
  const windowHeight = ref(0)
  const isMobile = ref(false)
  const isTablet = ref(false)
  const isDesktop = ref(false)
  const isTouchDevice = ref(false)
  const userAgent = ref('')

  // Computed breakpoint states
  const breakpoints = computed(() => ({
    sm: windowWidth.value >= mobileBreakpoints.sm,
    md: windowWidth.value >= mobileBreakpoints.md,
    lg: windowWidth.value >= mobileBreakpoints.lg,
    xl: windowWidth.value >= mobileBreakpoints.xl,
    '2xl': windowWidth.value >= mobileBreakpoints['2xl']
  }))

  // Device type detection
  const deviceType = computed(() => {
    if (isMobile.value) return 'mobile'
    if (isTablet.value) return 'tablet'
    return 'desktop'
  })

  // Screen orientation
  const orientation = computed(() => {
    return windowWidth.value > windowHeight.value ? 'landscape' : 'portrait'
  })

  // Secure user agent detection
  const detectUserAgent = () => {
    if (typeof window === 'undefined' || !window.navigator) {
      return ''
    }
    
    // Sanitize user agent to prevent XSS
    const ua = window.navigator.userAgent || ''
    return ua.replace(/[<>\"'&]/g, '')
  }

  // Mobile detection based on user agent
  const detectMobileFromUserAgent = (ua) => {
    if (!ua) return false
    
    return mobileUserAgentPatterns.some(pattern => pattern.test(ua))
  }

  // Touch device detection
  const detectTouchDevice = () => {
    if (typeof window === 'undefined') return false
    
    // Check for touch support
    const hasTouch = 'ontouchstart' in window || 
                    navigator.maxTouchPoints > 0 || 
                    navigator.msMaxTouchPoints > 0
    
    // Check user agent for touch indicators
    const ua = detectUserAgent()
    const hasTouchUA = touchDevicePatterns.some(pattern => pattern.test(ua))
    
    return hasTouch || hasTouchUA
  }

  // Device type detection based on screen size
  const detectDeviceType = (width) => {
    return {
      isMobile: width < mobileBreakpoints.md,
      isTablet: width >= mobileBreakpoints.md && width < mobileBreakpoints.lg,
      isDesktop: width >= mobileBreakpoints.lg
    }
  }

  // Update window dimensions
  const updateDimensions = () => {
    if (typeof window === 'undefined') return
    
    windowWidth.value = window.innerWidth
    windowHeight.value = window.innerHeight
    
    const deviceInfo = detectDeviceType(windowWidth.value)
    isMobile.value = deviceInfo.isMobile
    isTablet.value = deviceInfo.isTablet
    isDesktop.value = deviceInfo.isDesktop
  }

  // Initialize detection
  const initialize = () => {
    if (typeof window === 'undefined') return
    
    // Get user agent
    userAgent.value = detectUserAgent()
    
    // Detect touch device
    isTouchDevice.value = detectTouchDevice()
    
    // Update dimensions
    updateDimensions()
    
    // Override mobile detection with user agent if more accurate
    const uaMobile = detectMobileFromUserAgent(userAgent.value)
    if (uaMobile && !isMobile.value) {
      isMobile.value = true
      isTablet.value = false
      isDesktop.value = false
    }
  }

  // Responsive utility functions
  const isBreakpoint = (breakpoint) => {
    return breakpoints.value[breakpoint]
  }

  const isBreakpointUp = (breakpoint) => {
    return windowWidth.value >= mobileBreakpoints[breakpoint]
  }

  const isBreakpointDown = (breakpoint) => {
    return windowWidth.value < mobileBreakpoints[breakpoint]
  }

  const isBreakpointBetween = (min, max) => {
    return windowWidth.value >= mobileBreakpoints[min] && 
           windowWidth.value < mobileBreakpoints[max]
  }

  // Device-specific utilities
  const isIOS = computed(() => {
    return /iPad|iPhone|iPod/.test(userAgent.value)
  })

  const isAndroid = computed(() => {
    return /Android/.test(userAgent.value)
  })

  const isSafari = computed(() => {
    return /Safari/.test(userAgent.value) && !/Chrome/.test(userAgent.value)
  })

  const isChrome = computed(() => {
    return /Chrome/.test(userAgent.value) && !/Edge/.test(userAgent.value)
  })

  const isFirefox = computed(() => {
    return /Firefox/.test(userAgent.value)
  })

  const isEdge = computed(() => {
    return /Edge/.test(userAgent.value)
  })

  // Lifecycle hooks
  onMounted(() => {
    initialize()
    
    // Add resize listener with throttling
    let resizeTimeout
    const handleResize = () => {
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(updateDimensions, 100)
    }
    
    window.addEventListener('resize', handleResize)
    window.addEventListener('orientationchange', handleResize)
    
    // Cleanup function
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('orientationchange', handleResize)
      clearTimeout(resizeTimeout)
    })
  })

  return {
    // State
    windowWidth: readonly(windowWidth),
    windowHeight: readonly(windowHeight),
    isMobile: readonly(isMobile),
    isTablet: readonly(isTablet),
    isDesktop: readonly(isDesktop),
    isTouchDevice: readonly(isTouchDevice),
    userAgent: readonly(userAgent),
    
    // Computed
    breakpoints: readonly(breakpoints),
    deviceType: readonly(deviceType),
    orientation: readonly(orientation),
    
    // Browser detection
    isIOS: readonly(isIOS),
    isAndroid: readonly(isAndroid),
    isSafari: readonly(isSafari),
    isChrome: readonly(isChrome),
    isFirefox: readonly(isFirefox),
    isEdge: readonly(isEdge),
    
    // Utility functions
    isBreakpoint,
    isBreakpointUp,
    isBreakpointDown,
    isBreakpointBetween,
    
    // Methods
    updateDimensions,
    initialize
  }
}

// Global mobile detection instance
const rfpIsMobile = rfpUseIsMobile()

module.exports = {
  rfpUseIsMobile,
  rfpIsMobile,
  mobileBreakpoints: mobileBreakpoints
}
