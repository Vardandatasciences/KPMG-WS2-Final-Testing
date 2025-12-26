import axios from 'axios'
import { API_BASE_URL, MFA_ENABLED } from '../config/api.js'
import eventBus, { LOGOUT_EVENT, LOGIN_EVENT } from '../utils/eventBus.js'
 
class AuthService {
    constructor() {
        this.baseURL = API_BASE_URL
        this.accessToken = localStorage.getItem('access_token')
        this.refreshToken = localStorage.getItem('refresh_token')
        this.isLoggingOut = false // Flag to prevent refresh during logout
        this.isRefreshing = false // Flag to prevent multiple simultaneous refresh attempts
        this.failedRefreshAttempts = 0 // Track failed refresh attempts
        this.maxRefreshAttempts = 5 // Increased max attempts to be more lenient
        this.refreshInterval = null // Periodic refresh interval
        this.sessionCheckInterval = null // Periodic session check interval (for multi-session management)
        this.setupAxiosInterceptors()
        
        // Start periodic refresh if tokens exist (handles page reloads)
        // This ensures both Google SSO and normal login work the same
        const hasTokens = !!(localStorage.getItem('access_token') || localStorage.getItem('refresh_token'))
        if (hasTokens) {
            console.log('🔄 [AuthService] Tokens found on initialization - starting periodic refresh')
            this.startPeriodicTokenRefresh()
            this.startPeriodicSessionCheck()
        }
    }
 
    setupAxiosInterceptors() {
        // Request interceptor to add JWT token
        axios.interceptors.request.use(
            async (config) => {
                // Skip auth check for login/refresh/MFA/logout/Google OAuth endpoints
                const isAuthEndpoint = config.url && (
                    config.url.includes('/api/jwt/login/') ||
                    config.url.includes('/api/jwt/refresh/') ||
                    config.url.includes('/api/jwt/mfa/') ||
                    config.url.includes('/api/login/') ||
                    config.url.includes('/api/logout/') ||
                    config.url.includes('/api/jwt/logout/') ||
                    config.url.includes('/api/google/oauth/') ||
                    config.url.includes('/api/google/oauth-callback/')
                )
                
                // Don't block logout endpoint even if we're logging out
                if (this.isLoggingOut && !config.url.includes('/logout/')) {
                    return Promise.reject(new Error('Logging out'))
                }
               
                if (!isAuthEndpoint) {
                    // Check if token is expired and refresh if needed
                    await this.checkAndRefreshToken()
                   
                    const token = localStorage.getItem('access_token')
                    if (token) {
                        // Only check and refresh token if it's close to expiring (not on every request)
                        // This prevents unnecessary refresh attempts that could cause logout loops
                        const accessTokenExpires = localStorage.getItem('access_token_expires')
                        if (accessTokenExpires) {
                            const expirationTime = new Date(accessTokenExpires)
                            const currentTime = new Date()
                            const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime()
                            
                            // Only refresh if token expires in less than 10 minutes
                            if (timeUntilExpiration < 10 * 60 * 1000 && timeUntilExpiration > 0) {
                                // Token is close to expiring, try to refresh (but don't block the request if it fails)
                                this.checkAndRefreshToken().catch(err => {
                                    console.warn('⚠️ Token refresh check failed (non-blocking):', err.message)
                                })
                            }
                        }
                        
                        config.headers.Authorization = `Bearer ${token}`
                        // Reduced logging - only log for important requests
                        if (config.url.includes('/jwt/') || config.url.includes('/api/risk/')) {
                            console.log(`🔐 [AuthService] Adding JWT token to request: ${config.method.toUpperCase()} ${config.url}`)
                        }
                    } else {
                        // No token available - reject the request to prevent 401 errors
                        console.warn(`⚠️ [AuthService] No JWT token found for request: ${config.method.toUpperCase()} ${config.url} - blocking request`)
                        return Promise.reject(new Error('No authentication token available. Please login again.'))
                    }
                }
                return config
            },
            (error) => {
                return Promise.reject(error)
            }
        )
 
        // Response interceptor to handle 401 errors and refresh tokens
        axios.interceptors.response.use(
            (response) => {
                return response
            },
            async (error) => {
                const originalRequest = error.config
               
                // Handle network errors or missing config
                if (!originalRequest) {
                    console.error('❌ Request error: originalRequest is undefined')
                    return Promise.reject(error)
                }
               
                // CRITICAL: Don't try to refresh if the refresh endpoint itself failed
                // This prevents infinite loops when refresh token is invalid
                if (originalRequest.url && originalRequest.url.includes('/api/jwt/refresh/')) {
                    console.error('❌ Refresh endpoint returned 401 - refresh token is invalid/expired')
                    // Don't try to refresh again, just reject
                    return Promise.reject(error)
                }
               
                // Handle 401 errors (token expired)
                if (error.response && error.response.status === 401 && !originalRequest._retry) {
                    // Check if this is a session expiration (5-minute timeout)
                    const errorData = error.response.data || {}
                    if (errorData.session_expired === true || errorData.logout_reason === 'Session timeout after 5 minutes') {
                        console.log('⏰ Session expired after 5 minutes - redirecting to login')
                        // Clear all auth data
                        localStorage.removeItem('access_token')
                        localStorage.removeItem('refresh_token')
                        localStorage.removeItem('user_id')
                        localStorage.removeItem('user')
                        localStorage.removeItem('user_email')
                        localStorage.removeItem('user_name')
                        localStorage.removeItem('is_logged_in')
                        // Redirect to login immediately
                        if (window.location.pathname !== '/login') {
                            window.location.href = '/login'
                        }
                        return Promise.reject(error)
                    }
                    
                    // Don't try to refresh if we're already refreshing or logging out
                    if (this.isRefreshing || this.isLoggingOut) {
                        console.warn('⚠️ Refresh already in progress or logging out - skipping refresh attempt')
                        return Promise.reject(error)
                    }
                    
                    console.log('🔄 401 error detected - attempting token refresh...')
                    
                    // Mark this request as retried to prevent infinite loops
                    originalRequest._retry = true
                    
                    try {
                        // Attempt to refresh the token
                        const refreshSuccess = await this.refreshAccessToken()
                        
                        if (refreshSuccess) {
                            console.log('✅ Token refreshed successfully, retrying original request')
                            
                            // Update the authorization header with new token
                            const newToken = localStorage.getItem('access_token')
                            if (newToken) {
                                originalRequest.headers.Authorization = `Bearer ${newToken}`
                            }
                            
                            // Retry the original request
                            return axios(originalRequest)
                        } else {
                            console.warn('❌ Token refresh failed - user will need to login again')
                            // Don't force logout, let the user continue with limited access
                            return Promise.reject(error)
                        }
                    } catch (refreshError) {
                        console.error('❌ Error during token refresh:', refreshError)
                        // Don't force logout, let the user continue with limited access
                        return Promise.reject(error)
                    }
                }
               
                return Promise.reject(error)
            }
        )
    }
 
    async login(username, password, loginType = 'username', captchaToken = null) {
        console.log('🔥🔥🔥 [AuthService] LOGIN FUNCTION CALLED - NEW VERSION WITH INCIDENT FETCH 🔥🔥🔥');
        try {
            // Reset flags on login
            this.isLoggingOut = false
            this.isRefreshing = false
            this.failedRefreshAttempts = 0
           
            // ========================================
            // LICENSE VALIDATION PROCESS - AUTH SERVICE
            // ========================================
            // Step 1: Send login request to backend which will validate license
            console.log('🔐 LICENSE VALIDATION: Sending login request to backend for license validation...')
            const requestData = {
                username,
                password,
                login_type: loginType
            }
           
            // Include CAPTCHA token if provided (for username/userid login)
            if (captchaToken) {
                requestData.captcha_token = captchaToken
            }
           
            // Add timeout to prevent hanging requests (axios handles timeout internally)
            const response = await axios.post(`${this.baseURL}/api/jwt/login/`, requestData, {
                timeout: 30000 // 30 seconds timeout
            })
 
            // Handle MFA required response (only if MFA is enabled)
            if (MFA_ENABLED && response.data.status === 'mfa_required') {
                return {
                    success: false,
                    requiresMfa: true,
                    message: response.data.message || 'Please enter the verification code',
                    emailMasked: response.data.email_masked
                }
            }
 
            if (response.data.status === 'success') {
                const { access_token, refresh_token, access_token_expires, refresh_token_expires, user, license_verified } = response.data
               
                // Step 2: Check if license validation was successful from backend response
                console.log('🔐 LICENSE VALIDATION: Backend response received:', {
                    license_verified: license_verified,
                    has_license_key: !!user.license_key,
                    license_key_preview: user.license_key ? `${user.license_key.substring(0, 10)}...` : 'None'
                })
               
                // Store tokens
                localStorage.setItem('access_token', access_token)
                localStorage.setItem('refresh_token', refresh_token)
                localStorage.setItem('access_token_expires', access_token_expires)
                localStorage.setItem('refresh_token_expires', refresh_token_expires)
               
                // Store user info
                localStorage.setItem('user', JSON.stringify(user))
                localStorage.setItem('user_id', user.UserId.toString())
                localStorage.setItem('user_email', user.Email)
                localStorage.setItem('user_name', user.UserName)
                localStorage.setItem('user_full_name', `${user.FirstName} ${user.LastName}`)
                localStorage.setItem('isAuthenticated', 'true')
                localStorage.setItem('is_logged_in', 'true')
               
                // Update axios default headers
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
               
                // Initialize RBAC service
                try {
                    const { default: rbacService } = await import('./rbacService.js')
                    await rbacService.initialize()
                    console.log('🔐 RBAC service initialized after login')
                } catch (error) {
                    console.error('❌ Error initializing RBAC service:', error)
                }
                
                // ========================================
                // PREFETCH ALL DATA AFTER LOGIN (NON-BLOCKING)
                // ========================================
                // Start data prefetch asynchronously AFTER login completes
                // This ensures documents don't load during sign-in click
                console.log('🚀 [AuthService] Scheduling data prefetch after login...')
                
                // Use setTimeout to defer data fetching until after login completes
                setTimeout(async () => {
                    // Verify user is still authenticated before fetching
                    if (!this.isAuthenticated()) {
                        console.log('⚠️ [AuthService] User not authenticated, skipping data prefetch')
                        return
                    }
                    
                    console.log('🚀 [AuthService] Starting data prefetch for all services...')
                    const startTime = Date.now()
                    
                    try {
                        // Import all services (documents are loaded when DocumentHandling component mounts)
                        const [
                            { default: incidentService },
                            { default: riskDataService },
                            { default: integrationsDataService },
                            { default: treeDataService }
                        ] = await Promise.all([
                            import('./incidentService.js'),
                            import('./riskService.js'),
                            import('./integrationsService.js'),
                            import('./treeService.js')
                        ])
                        
                        console.log('✅ [AuthService] All services imported successfully')
                        
                        // Fetch all data in parallel (except documents - they load when component mounts)
                        const fetchPromises = {
                            incidents: incidentService.fetchAllIncidentData(user.UserId)
                                .then(result => {
                                    console.log(`✅ [AuthService] Incident data: ${incidentService.getData('incidents')?.length || 0} incidents`)
                                    localStorage.setItem('incident_data_fetched', 'true')
                                    return result
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Incident fetch error:', error.message)
                                    return { success: false, error: error.message }
                                }),
                            
                            risks: riskDataService.fetchAllRiskData()
                                .then(() => {
                                    const stats = riskDataService.getCacheStats()
                                    console.log(`✅ [AuthService] Risk data: ${stats.risksCount} risks, ${stats.riskInstancesCount} instances`)
                                    localStorage.setItem('risk_data_fetched', 'true')
                                    return { success: true }
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Risk fetch error:', error.message)
                                    return { success: false, error: error.message }
                                }),
                            
                            integrations: integrationsDataService.fetchAllIntegrationData()
                                .then(() => {
                                    const stats = integrationsDataService.getCacheStats()
                                    console.log(`✅ [AuthService] Integration data: ${stats.applicationsCount} applications, ${stats.connectedApplications} connected`)
                                    localStorage.setItem('integrations_data_fetched', 'true')
                                    return { success: true }
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Integrations fetch error:', error.message)
                                    return { success: false, error: error.message }
                                }),
                            
                            // Documents will be loaded when DocumentHandling component mounts
                            // Don't fetch here to avoid loading on sign-in click
                            documents: Promise.resolve({ success: true, skipped: true })
                                .then(() => {
                                    console.log('⏭️ [AuthService] Documents will be loaded when DocumentHandling component mounts')
                                    return { success: true, skipped: true }
                                }),
                            
                            tree: treeDataService.fetchAllTreeData()
                                .then(() => {
                                    const stats = treeDataService.getCacheStats()
                                    console.log(`✅ [AuthService] Tree data: ${stats.frameworksCount} frameworks`)
                                    localStorage.setItem('tree_data_fetched', 'true')
                                    return { success: true }
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Tree fetch error:', error.message)
                                    return { success: false, error: error.message }
                                })
                        }
                        
                        // Wait for all fetches to complete
                        const results = await Promise.allSettled([
                            fetchPromises.incidents,
                            fetchPromises.risks,
                            fetchPromises.integrations,
                            fetchPromises.documents,
                            fetchPromises.tree
                        ])
                        
                        const duration = Date.now() - startTime
                        const successCount = results.filter(r => r.status === 'fulfilled' && r.value?.success !== false).length
                        
                        console.log(`🎉 [AuthService] Data prefetch complete in ${duration}ms`)
                        console.log(`✅ [AuthService] ${successCount}/5 services fetched successfully`)
                        
                        // Store fetch completion time
                        localStorage.setItem('all_data_fetched', 'true')
                        localStorage.setItem('data_fetch_time', new Date().toISOString())
                        localStorage.setItem('data_fetch_duration', duration.toString())
                        
                        // Store promise globally for components
                        window.dataFetchPromise = Promise.resolve(results)
                        
                    } catch (error) {
                        console.error('❌ [AuthService] CRITICAL ERROR during data prefetch:', error)
                        console.error('❌ [AuthService] Error details:', error.stack)
                        localStorage.setItem('all_data_fetched', 'false')
                    }
                }, 100) // Small delay to ensure login completes first
                
                // Start periodic token refresh
                this.startPeriodicTokenRefresh()
                // Start periodic session check (for multi-session management)
                this.startPeriodicSessionCheck()
                
                // Emit login event
                eventBus.emit(LOGIN_EVENT, { user })
               
                console.log('🔐 JWT Login successful!', {
                    user_id: user.UserId,
                    email: user.Email,
                    username: user.UserName
                })
               
                // Step 3: Return success with license validation status
                console.log('✅ LICENSE VALIDATION: Returning successful login with license verification status')
                return {
                    success: true,
                    user,
                    license_verified: license_verified, // Include license validation status
                    tokens: {
                        access: access_token,
                        refresh: refresh_token,
                        access_token_expires: access_token_expires,
                        refresh_token_expires: refresh_token_expires
                    }
                }
            } else {
                throw new Error(response.data.message || 'Login failed')
            }
        } catch (error) {
            console.error('❌ JWT Login error:', error)
           
            // Handle specific error types
            if (error.code === 'ECONNREFUSED' || error.message?.includes('CONNECTION_REFUSED') || error.message?.includes('Network Error')) {
                throw new Error('Unable to connect to the server. Please ensure the backend server is running on port 8000.')
            } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Timeout')) {
                throw new Error('Request timed out. The server may be slow or unavailable. Please try again.')
            } else if (error.response) {
                // Server responded with error
                throw new Error(error.response.data?.message || error.message || 'Login failed')
            } else {
                // Network or other error
                throw new Error(error.message || 'Unable to connect to server. Please check your connection.')
            }
        }
    }

    async verifyMfaOtp(username, password, otp, loginType = 'username') {
        // Verify MFA OTP and complete login
        try {
            console.log('🔐 [AuthService] Verifying MFA OTP...')
           
            // Add timeout to prevent hanging requests (axios handles timeout internally)
            const response = await axios.post(`${this.baseURL}/api/jwt/mfa/verify-otp/`, {
                username,
                password,
                otp,
                login_type: loginType
            }, {
                timeout: 30000 // 30 seconds timeout
            })
 
            if (response.data.status === 'success') {
                const { access_token, refresh_token, access_token_expires, refresh_token_expires, user, license_verified } = response.data
               
                // Store tokens
                localStorage.setItem('access_token', access_token)
                localStorage.setItem('refresh_token', refresh_token)
                localStorage.setItem('access_token_expires', access_token_expires)
                localStorage.setItem('refresh_token_expires', refresh_token_expires)
               
                // Store user info
                localStorage.setItem('user', JSON.stringify(user))
                localStorage.setItem('user_id', user.UserId.toString())
                localStorage.setItem('user_email', user.Email)
                localStorage.setItem('user_name', user.UserName)
                localStorage.setItem('user_full_name', `${user.FirstName} ${user.LastName}`)
                localStorage.setItem('isAuthenticated', 'true')
                localStorage.setItem('is_logged_in', 'true')
               
                // Update axios default headers
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
               
                // Initialize RBAC service
                try {
                    const { default: rbacService } = await import('./rbacService.js')
                    await rbacService.initialize()
                    console.log('🔐 RBAC service initialized after MFA login')
                } catch (error) {
                    console.error('❌ Error initializing RBAC service:', error)
                }
               
                // Start periodic token refresh
                this.startPeriodicTokenRefresh()
                // Start periodic session check (for multi-session management)
                this.startPeriodicSessionCheck()
               
                // Emit login event
                eventBus.emit(LOGIN_EVENT, { user })
               
                console.log('🔐 MFA Login successful!', {
                    user_id: user.UserId,
                    email: user.Email,
                    username: user.UserName
                })
               
                return {
                    success: true,
                    user,
                    license_verified: license_verified,
                    tokens: {
                        access: access_token,
                        refresh: refresh_token,
                        access_token_expires: access_token_expires,
                        refresh_token_expires: refresh_token_expires
                    }
                }
            } else {
                throw new Error(response.data.message || 'MFA verification failed')
            }
        } catch (error) {
            console.error('❌ MFA OTP verification error:', error)
           
            // Handle specific error types
            if (error.code === 'ECONNREFUSED' || error.message?.includes('CONNECTION_REFUSED') || error.message?.includes('Network Error')) {
                throw new Error('Unable to connect to the server. Please ensure the backend server is running.')
            } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Timeout')) {
                throw new Error('Request timed out. Please try again.')
            } else if (error.response && error.response.data) {
                throw new Error(error.response.data.message || 'MFA verification failed')
            } else {
                throw new Error(error.message || 'MFA verification failed. Please try again.')
            }
        }
    }
 
    async resendMfaOtp(username, password, loginType = 'username') {
        // Resend MFA OTP to user's email
        try {
            console.log('🔐 [AuthService] Resending MFA OTP...')
           
            // Add timeout to prevent hanging requests (axios handles timeout internally)
            const response = await axios.post(`${this.baseURL}/api/jwt/mfa/resend-otp/`, {
                username,
                password,
                login_type: loginType
            }, {
                timeout: 30000 // 30 seconds timeout
            })
 
            if (response.data.status === 'success') {
                return {
                    success: true,
                    message: response.data.message || 'New verification code sent',
                    emailMasked: response.data.email_masked
                }
            } else {
                throw new Error(response.data.message || 'Failed to resend OTP')
            }
        } catch (error) {
            console.error('❌ MFA resend OTP error:', error)
           
            // Handle specific error types
            if (error.code === 'ECONNREFUSED' || error.message?.includes('CONNECTION_REFUSED') || error.message?.includes('Network Error')) {
                throw new Error('Unable to connect to the server. Please ensure the backend server is running.')
            } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Timeout')) {
                throw new Error('Request timed out. Please try again.')
            } else if (error.response && error.response.data) {
                throw new Error(error.response.data.message || 'Failed to resend OTP')
            } else {
                throw new Error(error.message || 'Failed to resend OTP. Please try again.')
            }
        }
    }
 
 
    async checkAndRefreshToken() {
        try {
            // First check if we have an access token at all
            const accessToken = localStorage.getItem('access_token')
            const refreshToken = localStorage.getItem('refresh_token')
            
            if (!accessToken) {
                // No token available, can't refresh
                return false
            }
            
            // If we have a refresh token but no access token expiration, try to refresh
            // This handles cases where expiration info might be missing
            const accessTokenExpires = localStorage.getItem('access_token_expires')
            if (!accessTokenExpires) {
                // Token exists but no expiration info - check if we have refresh token
                if (refreshToken) {
                    console.warn('⚠️ No access token expiration found, but refresh token exists - attempting refresh...')
                    return await this.refreshAccessToken()
                } else {
                    console.warn('⚠️ No access token expiration found and no refresh token - cannot refresh')
                    return false
                }
            }

            // Parse expiration time - handle both ISO strings and timestamps
            let expirationTime
            try {
                expirationTime = new Date(accessTokenExpires)
                if (isNaN(expirationTime.getTime())) {
                    // Invalid date, try to refresh if we have refresh token
                    console.warn('⚠️ Invalid access token expiration date, attempting refresh...')
                    if (refreshToken) {
                        return await this.refreshAccessToken()
                    }
                    return false
                }
            } catch (e) {
                console.warn('⚠️ Error parsing access token expiration, attempting refresh...')
                if (refreshToken) {
                    return await this.refreshAccessToken()
                }
                return false
            }

            const currentTime = new Date()
            const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime()
           
            // Refresh token if it expires in less than 10 minutes (same as normal login)
            if (timeUntilExpiration < 10 * 60 * 1000) {
                console.log('🔄 Access token expires soon, refreshing...')
                return await this.refreshAccessToken()
            }
           
            return false
        } catch (error) {
            console.error('❌ Error checking token expiration:', error)
            // Don't throw - return false so periodic refresh continues
            return false
        }
    }
 
    async refreshAccessToken() {
        try {
            // Don't refresh if we're logging out or already refreshing
            if (this.isLoggingOut || this.isRefreshing) {
                console.log('🛑 Refresh blocked: isLoggingOut=' + this.isLoggingOut + ', isRefreshing=' + this.isRefreshing)
                return false
            }

            // Check if we've exceeded max refresh attempts
            // But don't immediately clear - check if tokens are actually expired first
            if (this.failedRefreshAttempts >= this.maxRefreshAttempts) {
                // Check if tokens are still valid before forcing logout
                const accessToken = localStorage.getItem('access_token')
                const accessTokenExpires = localStorage.getItem('access_token_expires')
                const refreshToken = localStorage.getItem('refresh_token')
                const refreshTokenExpires = localStorage.getItem('refresh_token_expires')
                
                let tokensExpired = true
                
                // Check refresh token
                if (refreshToken && refreshTokenExpires) {
                    try {
                        const refreshExpirationTime = new Date(refreshTokenExpires)
                        if (!isNaN(refreshExpirationTime.getTime())) {
                            if (refreshExpirationTime.getTime() > Date.now()) {
                                tokensExpired = false
                            }
                        }
                    } catch (e) {
                        // Can't parse - assume still valid
                        tokensExpired = false
                    }
                } else if (refreshToken) {
                    // Have token but no expiration - assume valid
                    tokensExpired = false
                }
                
                // Check access token
                if (tokensExpired && accessToken && accessTokenExpires) {
                    try {
                        const accessExpirationTime = new Date(accessTokenExpires)
                        if (!isNaN(accessExpirationTime.getTime())) {
                            if (accessExpirationTime.getTime() > Date.now()) {
                                tokensExpired = false
                            }
                        }
                    } catch (e) {
                        // Can't parse - assume still valid
                        tokensExpired = false
                    }
                }
                
                if (tokensExpired) {
                    console.error('❌ Max refresh attempts exceeded AND tokens expired - logging out')
                    this.clearAuthData(true) // Redirect to login
                } else {
                    console.warn('⚠️ Max refresh attempts exceeded but tokens still valid - will retry later')
                    // Reset counter after delay
                    setTimeout(() => {
                        this.failedRefreshAttempts = Math.max(0, this.failedRefreshAttempts - 1)
                    }, 30 * 60 * 1000) // Reset after 30 minutes
                }
                return false
            }

            this.isRefreshing = true

            const refreshToken = localStorage.getItem('refresh_token')
            if (!refreshToken) {
                console.error('❌ No refresh token available')
                this.failedRefreshAttempts++
                this.isRefreshing = false
                throw new Error('No refresh token available')
            }
 
            // Use a timeout to prevent hanging requests (increased to 30 seconds)
            const refreshPromise = axios.post(`${this.baseURL}/api/jwt/refresh/`, {
                refresh_token: refreshToken
            }, {
                timeout: 30000 // 30 seconds timeout for token refresh
            })
            
            const response = await refreshPromise
 
            if (response.data.status === 'success') {
                const { access_token, refresh_token, access_token_expires, refresh_token_expires } = response.data
               
                // Update stored tokens - CRITICAL: Also update refresh token (token rotation)
                localStorage.setItem('access_token', access_token)
                localStorage.setItem('access_token_expires', access_token_expires)
                
                // BUGFIX: Save new refresh token to prevent 401 loop
                // Backend rotates refresh tokens for security, so we must save the new one
                if (refresh_token) {
                    localStorage.setItem('refresh_token', refresh_token)
                    console.log('🔄 Refresh token updated (token rotation)')
                }
                if (refresh_token_expires) {
                    localStorage.setItem('refresh_token_expires', refresh_token_expires)
                }
               
                // Update axios default headers
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
               
                // Reset failed attempts counter on success
                this.failedRefreshAttempts = 0
                
                console.log('🔄 JWT token refreshed successfully')
                return true
            } else {
                this.failedRefreshAttempts++
                throw new Error(response.data.message || 'Token refresh failed')
            }
        } catch (error) {
            console.error('❌ JWT token refresh error:', error)
            
            // Handle timeout errors specifically
            if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Timeout')) {
                console.warn('⚠️ Token refresh timed out - this may be due to slow network or server load')
                // Don't increment failed attempts for timeout errors - they're often temporary
                this.isRefreshing = false
                return false
            }
            
            // Only increment failed attempts for actual errors, not if we're already refreshing
            if (!this.isRefreshing) {
                this.failedRefreshAttempts++
            }
            
            // Check if access token is still valid before logging out (same for Google SSO and normal login)
            const accessToken = localStorage.getItem('access_token')
            const accessTokenExpires = localStorage.getItem('access_token_expires')
            const refreshToken = localStorage.getItem('refresh_token')
            
            // If we still have a refresh token, don't log out - try again later
            if (refreshToken) {
                console.log('⚠️ Refresh failed but refresh token exists - will retry on next check...')
                this.isRefreshing = false
                // Reset failed attempts after some time to allow retry
                setTimeout(() => {
                    if (this.failedRefreshAttempts > 0) {
                        this.failedRefreshAttempts = Math.max(0, this.failedRefreshAttempts - 1)
                    }
                }, 5 * 60 * 1000) // Reset after 5 minutes
                return false
            }
            
            if (accessToken && accessTokenExpires) {
                try {
                    const expirationTime = new Date(accessTokenExpires)
                    if (!isNaN(expirationTime.getTime())) {
                        const currentTime = new Date()
                        const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime()
                        
                        // If access token is still valid for more than 1 minute, don't log out
                        if (timeUntilExpiration > 60 * 1000) {
                            console.log('⚠️ Refresh failed but access token still valid, continuing...')
                            this.isRefreshing = false
                            return false
                        }
                    }
                } catch (e) {
                    // Invalid expiration date, but don't log out if we have refresh token
                    if (refreshToken) {
                        console.log('⚠️ Refresh failed but refresh token exists - will retry...')
                        this.isRefreshing = false
                        return false
                    }
                }
            }
            
            // IMPORTANT: Same behavior for Google SSO and normal login
            // Only log out if refresh token is actually expired, not just because refresh failed
            // Network issues or temporary server problems shouldn't log out users
            
            if (this.failedRefreshAttempts >= this.maxRefreshAttempts) {
                // Check if refresh token is actually expired before logging out
                const refreshTokenExpires = localStorage.getItem('refresh_token_expires')
                let refreshTokenExpired = true
                
                if (refreshToken && refreshTokenExpires) {
                    try {
                        const refreshExpirationTime = new Date(refreshTokenExpires)
                        if (!isNaN(refreshExpirationTime.getTime())) {
                            refreshTokenExpired = refreshExpirationTime.getTime() <= Date.now()
                        } else {
                            // Can't parse expiration - assume still valid if token exists
                            refreshTokenExpired = false
                        }
                    } catch (e) {
                        // Can't parse - assume still valid
                        refreshTokenExpired = false
                    }
                } else if (refreshToken) {
                    // Have refresh token but no expiration - assume still valid
                    refreshTokenExpired = false
                }
                
                // Also check if access token is expired
                let accessTokenExpired = true
                if (accessToken && accessTokenExpires) {
                    try {
                        const accessExpirationTime = new Date(accessTokenExpires)
                        if (!isNaN(accessExpirationTime.getTime())) {
                            accessTokenExpired = accessExpirationTime.getTime() <= Date.now()
                        } else {
                            accessTokenExpired = false
                        }
                    } catch (e) {
                        accessTokenExpired = false
                    }
                }
                
                // Only log out if BOTH tokens are expired/invalid
                if (refreshTokenExpired && accessTokenExpired) {
                    console.error('❌ Both access and refresh tokens expired - logging out')
                    this.clearAuthData(true) // Redirect to login
                } else {
                    console.warn('⚠️ Max refresh attempts reached but tokens still valid - keeping user logged in (same as normal login)')
                    // Reset counter after delay to allow retry
                    setTimeout(() => {
                        this.failedRefreshAttempts = 0
                    }, 30 * 60 * 1000) // Reset after 30 minutes
                }
            }
            
            this.isRefreshing = false
            return false
        } finally {
            // Ensure isRefreshing is always reset
            if (this.isRefreshing) {
                this.isRefreshing = false
            }
        }
    }
 
    async logout() {
        try {
            console.log('🚪 [AuthService] Starting logout process...')
            // Set logout flag to prevent refresh attempts
            this.isLoggingOut = true
            this.isRefreshing = false
           
            // Emit logout event before clearing data
            eventBus.emit(LOGOUT_EVENT, {})
           
            const token = localStorage.getItem('access_token')
            const userId = localStorage.getItem('user_id')
            const userName = localStorage.getItem('user_name')
            
            console.log('🚪 [AuthService] Logout - Token exists:', !!token, 'User ID:', userId, 'User Name:', userName)
            console.log('🚪 [AuthService] Calling logout endpoint:', `${this.baseURL}/api/jwt/logout/`)
            
            // Always try to call logout endpoint, even if token is missing
            // This ensures the backend can log the logout attempt
            try {
                const headers = {}
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`
                }
                
                const response = await axios.post(`${this.baseURL}/api/jwt/logout/`, {}, {
                    headers: headers
                })
                console.log('✅ [AuthService] Logout API call successful:', response.data)
            } catch (apiError) {
                console.error('❌ [AuthService] Logout API call failed:', apiError.response?.status, apiError.response?.data || apiError.message)
                // Continue with cleanup even if API call fails
            }
        } catch (error) {
            console.error('❌ [AuthService] Logout error:', error)
            console.warn('⚠️ [AuthService] Logout API call failed, but continuing with local cleanup:', error)
        } finally {
            // Clear all stored data (don't auto-redirect, let logout flow handle it)
            this.clearAuthData(false)
            // Reset flags
            this.isLoggingOut = false
            this.isRefreshing = false
            this.failedRefreshAttempts = 0
            console.log('🧹 [AuthService] Logout cleanup completed')
        }
    }
 
    forceLogout() {
        // COMPLETELY DISABLED: No automatic logout
        console.log('🛡️ Force logout disabled - user will not be logged out automatically')
        // Do nothing - user stays logged in
    }
 
    clearAuthData(shouldRedirect = true) {
        // Stop periodic refresh
        this.stopPeriodicTokenRefresh()
        // Stop periodic session check
        this.stopPeriodicSessionCheck()
       
        // Clear tokens
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('access_token_expires')
        localStorage.removeItem('refresh_token_expires')
       
        // Clear user data
        localStorage.removeItem('user')
        localStorage.removeItem('user_id')
        localStorage.removeItem('user_email')
        localStorage.removeItem('user_name')
        localStorage.removeItem('user_full_name')
        localStorage.removeItem('isAuthenticated')
        localStorage.removeItem('is_logged_in')
        localStorage.removeItem('remember_me')
       
        // Clear axios headers
        delete axios.defaults.headers.common['Authorization']
       
        // Clear RBAC service data
        try {
            const { default: rbacService } = require('./rbacService.js')
            rbacService.clearUserData()
        } catch (error) {
            console.error('❌ Error clearing RBAC data:', error)
        }
       
        // Clear all service data
        try {
            const { default: incidentService } = require('./incidentService.js')
            incidentService.clearCache()
            console.log('🧹 Incident service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Incident data:', error)
        }
        
        try {
            const { default: riskDataService } = require('./riskService.js')
            riskDataService.clearCache()
            console.log('🧹 Risk service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Risk data:', error)
        }
        
        try {
            const { default: integrationsDataService } = require('./integrationsService.js')
            integrationsDataService.clearCache()
            console.log('🧹 Integrations service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Integrations data:', error)
        }
        
        try {
            const { default: documentDataService } = require('./documentService.js')
            documentDataService.clearCache()
            console.log('🧹 Document service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Document data:', error)
        }
        
        try {
            const { default: treeDataService } = require('./treeService.js')
            treeDataService.clearCache()
            console.log('🧹 Tree service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Tree data:', error)
        }
       
        console.log('🧹 Auth data cleared')
        
        // Redirect to login if requested (default: true)
        // Only redirect if not already on login page and not during explicit logout
        if (shouldRedirect && window.location.pathname !== '/login' && window.location.pathname !== '/') {
            console.log('🔄 Redirecting to login page...')
            // Use setTimeout to allow cleanup to complete first
            setTimeout(() => {
                window.location.href = '/login'
            }, 100)
        }
    }
   
    startPeriodicTokenRefresh() {
        // Check if we have tokens (access or refresh) - start refresh even if user object is missing
        const accessToken = localStorage.getItem('access_token')
        const refreshToken = localStorage.getItem('refresh_token')
        
        if (!accessToken && !refreshToken) {
            console.log('⚠️ No tokens found, skipping periodic token refresh')
            return
        }
       
        // Clear any existing interval
        this.stopPeriodicTokenRefresh()
       
        // Check token every 5 minutes (300 seconds) - less aggressive refresh
        this.refreshInterval = setInterval(async () => {
            try {
                // Check if we still have tokens before attempting refresh
                const currentAccessToken = localStorage.getItem('access_token')
                const currentRefreshToken = localStorage.getItem('refresh_token')
                
                if (!currentAccessToken && !currentRefreshToken) {
                    console.log('⚠️ Tokens cleared, stopping periodic refresh')
                    this.stopPeriodicTokenRefresh()
                    return
                }
                
                // Reduced logging - only log when actually refreshing
                await this.checkAndRefreshToken()
            } catch (error) {
                console.error('❌ Error in periodic token refresh:', error)
            }
        }, 5 * 60 * 1000) // 5 minutes instead of 2 minutes
       
        console.log('🔄 Periodic token refresh started')
    }
   
    stopPeriodicTokenRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval)
            this.refreshInterval = null
            console.log('🛑 Periodic token refresh stopped')
        }
    }

    startPeriodicSessionCheck() {
        // Check if we have tokens before starting session check
        const accessToken = localStorage.getItem('access_token')
        
        if (!accessToken) {
            console.log('⚠️ No access token found, skipping periodic session check')
            return
        }
        
        // Clear any existing interval
        this.stopPeriodicSessionCheck()
        
        // Check session every 5 seconds (for multi-session management)
        // This detects when user logs in from another location
        this.sessionCheckInterval = setInterval(async () => {
            try {
                // Check if we still have tokens before attempting verification
                const currentAccessToken = localStorage.getItem('access_token')
                
                if (!currentAccessToken) {
                    console.log('⚠️ Access token cleared, stopping periodic session check')
                    this.stopPeriodicSessionCheck()
                    return
                }
                
                // Verify token - this checks if session is still valid
                // verifyToken throws on 401, returns false on other errors, returns true on success
                try {
                    const isValid = await this.verifyToken()
                    if (!isValid) {
                        // Non-401 error (network, etc.) - don't logout, just log
                        console.warn('⚠️ Session check failed (non-401 error) - will retry')
                    }
                    // If isValid is true, session is still valid - do nothing
                } catch (error) {
                    // If verification fails with 401, it means session is invalid
                    if (error.response && error.response.status === 401) {
                        console.warn('⚠️ Session check returned 401 - session invalidated')
                        this.handleSessionInvalidated()
                    } else {
                        // Other errors (network, etc.) - don't logout, just log
                        console.warn('⚠️ Session check error (will retry):', error.message)
                    }
                }
            } catch (error) {
                // Catch any unexpected errors in the outer try block
                console.error('❌ Unexpected error in periodic session check:', error)
            }
        }, 5 * 1000) // Check every 5 seconds
        
        console.log('🔐 Periodic session check started (every 5 seconds)')
    }

    stopPeriodicSessionCheck() {
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval)
            this.sessionCheckInterval = null
            console.log('🛑 Periodic session check stopped')
        }
    }

    handleSessionInvalidated() {
        console.warn('🚪 Session invalidated - logging out and redirecting to login')
        // Stop periodic checks to prevent loops
        this.stopPeriodicSessionCheck()
        this.stopPeriodicTokenRefresh()
        
        // Clear auth data and redirect
        this.clearAuthData(true)
    }
 
    async verifyToken() {
        try {
            const token = localStorage.getItem('access_token')
            if (!token) {
                return false
            }

            const response = await axios.get(`${this.baseURL}/api/jwt/verify/`, {
                headers: { Authorization: `Bearer ${token}` }
            })

            return response.data.status === 'success'
        } catch (error) {
            // Re-throw error so caller can check status code
            if (error.response && error.response.status === 401) {
                throw error
            }
            console.error('❌ Token verification failed:', error)
            return false
        }
    }
 
    isAuthenticated() {
        // Check if user has valid authentication data
        const token = localStorage.getItem('access_token')
        const user = localStorage.getItem('user')
        const isLoggedIn = localStorage.getItem('is_logged_in')
       
        const isAuth = !!(token && user && isLoggedIn === 'true')
        console.log(`🔐 [AuthService] Authentication check: ${isAuth} (token: ${!!token}, user: ${!!user}, logged_in: ${isLoggedIn})`)
        return isAuth
    }
 
    getCurrentUser() {
        const userStr = localStorage.getItem('user')
        return userStr ? JSON.parse(userStr) : null
    }
 
    getAccessToken() {
        return localStorage.getItem('access_token')
    }
 
    getRefreshToken() {
        return localStorage.getItem('refresh_token')
    }
 
    isNonCriticalEndpoint(url) {
        // List of endpoints that should not trigger logout on 401 errors
        const nonCriticalEndpoints = [
            '/api/frameworks/',
            '/api/policy-categories/',
            '/api/user-role/',
            '/api/entities/',
            '/api/users/',
            '/api/departments/',
            '/api/users-for-reviewer-selection/',
            '/api/notifications/',
            '/api/current-user/',
            '/api/custom-users/',
            '/api/get-notifications/',
            '/api/policies/',
            '/api/compliance/',
            '/api/incident/',
            '/api/risk/',
            '/api/audit/',
            '/api/all-policies/',
            '/api/framework-versions/',
            '/api/policy-versions/',
            '/api/subpolicies/',
            '/api/compliances/',
            '/api/rbac/roles/',
            '/api/rbac/users-for-dropdown/',
            '/api/rbac/permissions/',
            '/api/rbac/user-permissions/'
        ]
       
        return nonCriticalEndpoints.some(endpoint => url.includes(endpoint))
    }
 
    // Legacy session-based authentication (for backward compatibility)
    async sessionLogin(username, password, loginType = 'username') {
        try {
            const response = await axios.post(`${this.baseURL}/api/login/`, {
                username,
                password,
                login_type: loginType
            })
 
            if (response.data && response.data.user) {
                localStorage.setItem('isAuthenticated', 'true')
                localStorage.setItem('user', JSON.stringify(response.data.user))
                localStorage.setItem('user_id', response.data.user.id.toString())
                localStorage.setItem('user_email', response.data.user.email)
                localStorage.setItem('user_name', response.data.user.username)
                localStorage.setItem('user_full_name', `${response.data.user.firstName} ${response.data.user.lastName}`)
                localStorage.setItem('is_logged_in', 'true')
               
                console.log('🔐 Session Login successful!', {
                    user_id: response.data.user.id,
                    email: response.data.user.email,
                    username: response.data.user.username
                })
               
                return {
                    success: true,
                    user: response.data.user
                }
            } else {
                throw new Error('Invalid response from server')
            }
        } catch (error) {
            console.error('❌ Session Login error:', error)
            throw error
        }
    }
 
    async sessionLogout() {
        try {
            await axios.post(`${this.baseURL}/api/logout/`)
        } catch (error) {
            console.warn('Session logout API call failed, but continuing with local cleanup:', error)
        } finally {
            this.clearAuthData(false) // Don't auto-redirect for explicit logout
        }
    }



    

    /**
     * Initiate Google OAuth SSO login
     */
    async initiateGoogleOAuth() {
        try {
            console.log('🔐 [AuthService] Initiating Google OAuth SSO...')
            const response = await axios.get(`${this.baseURL}/api/google/oauth/`)
            
            if (response.data.status === 'success' && response.data.authorization_url) {
                // Redirect to Google OAuth page
                window.location.href = response.data.authorization_url
            } else {
                throw new Error(response.data.message || 'Failed to initiate Google OAuth')
            }
        } catch (error) {
            console.error('❌ Google OAuth initiate error:', error)
            if (error.response && error.response.data) {
                throw new Error(error.response.data.message || 'Failed to initiate Google OAuth')
            }
            throw error
        }
    }

    /**
     * Handle Google OAuth callback and complete login
     * This is called when the user is redirected back from Google
     */
    async handleGoogleOAuthCallback(accessToken, refreshToken, userId, consentRequired, accessTokenExpires, refreshTokenExpires) {
        try {
            console.log('🔐 [AuthService] Handling Google OAuth callback...')
            
            // Store tokens with expiration times (same as normal login)
            localStorage.setItem('access_token', accessToken)
            localStorage.setItem('refresh_token', refreshToken)
            
            // Store expiration times - ensure they're in ISO format (same as normal login)
            if (accessTokenExpires) {
                // Convert to ISO string if it's not already
                const expiresDate = new Date(accessTokenExpires)
                if (!isNaN(expiresDate.getTime())) {
                    localStorage.setItem('access_token_expires', expiresDate.toISOString())
                } else {
                    localStorage.setItem('access_token_expires', accessTokenExpires)
                }
            }
            if (refreshTokenExpires) {
                // Convert to ISO string if it's not already
                const expiresDate = new Date(refreshTokenExpires)
                if (!isNaN(expiresDate.getTime())) {
                    localStorage.setItem('refresh_token_expires', expiresDate.toISOString())
                } else {
                    localStorage.setItem('refresh_token_expires', refreshTokenExpires)
                }
            }
            
            console.log('✅ [AuthService] Google SSO tokens stored:', {
                hasAccessToken: !!accessToken,
                hasRefreshToken: !!refreshToken,
                accessTokenExpires: accessTokenExpires,
                refreshTokenExpires: refreshTokenExpires,
                accessTokenExpiresParsed: accessTokenExpires ? new Date(accessTokenExpires).toISOString() : null,
                refreshTokenExpiresParsed: refreshTokenExpires ? new Date(refreshTokenExpires).toISOString() : null
            })
            
            // Verify tokens are actually stored
            const storedAccessToken = localStorage.getItem('access_token')
            const storedRefreshToken = localStorage.getItem('refresh_token')
            if (!storedAccessToken || !storedRefreshToken) {
                console.error('❌ [AuthService] CRITICAL: Tokens not properly stored!', {
                    storedAccessToken: !!storedAccessToken,
                    storedRefreshToken: !!storedRefreshToken
                })
            }
            
            // Fetch user info to complete login
            const userResponse = await axios.get(`${this.baseURL}/api/jwt/verify/`, {
                headers: { Authorization: `Bearer ${accessToken}` }
            })
            
            if (userResponse.data.status === 'success' && userResponse.data.user) {
                const user = userResponse.data.user
                
                // Store user info (same as regular login)
                localStorage.setItem('user', JSON.stringify(user))
                localStorage.setItem('user_id', user.UserId.toString())
                localStorage.setItem('user_email', user.Email)
                localStorage.setItem('user_name', user.UserName)
                localStorage.setItem('user_full_name', `${user.FirstName} ${user.LastName}`)
                localStorage.setItem('isAuthenticated', 'true')
                localStorage.setItem('is_logged_in', 'true')
                
                // Update axios default headers
                axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
                
                // Initialize RBAC service
                try {
                    const { default: rbacService } = await import('./rbacService.js')
                    await rbacService.initialize()
                    console.log('🔐 RBAC service initialized after Google SSO login')
                } catch (error) {
                    console.error('❌ Error initializing RBAC service:', error)
                }
                
                // Start periodic token refresh (same as normal login)
                console.log('🔄 [AuthService] Starting periodic token refresh for Google SSO user')
                this.startPeriodicTokenRefresh()
                // Start periodic session check (for multi-session management)
                this.startPeriodicSessionCheck()
                
                // Verify periodic refresh started
                setTimeout(() => {
                    if (!this.refreshInterval) {
                        console.error('❌ [AuthService] CRITICAL: Periodic refresh did not start!')
                        // Try again
                        this.startPeriodicTokenRefresh()
                    } else {
                        console.log('✅ [AuthService] Periodic token refresh confirmed running')
                    }
                }, 1000)
                
                // Emit login event (this triggers navbar/sidebar updates)
                eventBus.emit(LOGIN_EVENT, { user })
                
                // Dispatch auth changed event (for components listening to auth state)
                window.dispatchEvent(new Event('authChanged'))
                
                // Call global login success handler if it exists
                if (window.onSuccessfulLogin) {
                    window.onSuccessfulLogin()
                }
                
                console.log('🔐 Google SSO Login successful!', {
                    user_id: user.UserId,
                    email: user.Email,
                    username: user.UserName
                })
                
                return {
                    success: true,
                    user,
                    consent_required: consentRequired === 'true' || consentRequired === true
                }
            } else {
                throw new Error('Failed to verify user after Google OAuth')
            }
        } catch (error) {
            console.error('❌ Google OAuth callback error:', error)
            throw error
        }
    }
}
 
// Create singleton instance
const authService = new AuthService()
 
export default authService