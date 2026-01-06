<template>
  <div class="min-h-screen bg-background">
    <div class="container mx-auto px-4 py-6 max-w-7xl space-y-6">
    <!-- Search View -->
    <div v-if="currentView === 'search'">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div class="space-y-2">
          <h1 class="text-3xl font-bold text-foreground">Global Search</h1>
          <p class="text-base text-muted-foreground">Search across all TPRM modules</p>
        </div>
        <div class="flex gap-3">
          <Button
            variant="outline"
            @click="handleViewAnalytics"
            class="gap-2"
          >
            <BarChart3 class="w-4 h-4" />
            View Analytics
          </Button>
          <SearchHistory_TPRM ref="searchHistoryRef" @select-query="handleHistorySelect" />
        </div>
      </div>

      <!-- Search Filters -->
      <Card class="shadow-sm">
        <CardContent class="p-6">
          <SearchFilters_TPRM v-model="activeFilters" @update:model-value="handleFilterChange" />
        </CardContent>
      </Card>

      <!-- Search Input -->
      <Card class="shadow-sm">
        <CardContent class="p-6">
          <div class="relative max-w-2xl mx-auto">
            <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              placeholder="Search across all modules..."
              class="pl-12 h-12 text-base"
              @input="handleSearchInput"
              @keyup.enter="finalizeSearch"
              :disabled="isLoading"
            />
          </div>
        </CardContent>
      </Card>

      <!-- Search Results -->
      <div v-if="searchQuery || searchResults" class="mt-8">
        <!-- Results Header -->
        <div class="flex justify-between items-center mb-6 px-1">
          <div>
            <span class="text-xl font-semibold">
              {{ searchResults?.total || 0 }} results found
            </span>
            <span v-if="searchQuery" class="text-sm text-muted-foreground ml-2">
              for "{{ searchQuery }}"
            </span>
            <span v-if="isTyping" class="text-sm text-primary ml-2">
              <Loader2 class="inline h-4 w-4 animate-spin mr-1" />
              Searching...
            </span>
            <span v-else-if="isLoading" class="text-sm text-primary ml-2">
              <Loader2 class="inline h-4 w-4 animate-spin mr-1" />
              Loading...
            </span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading && !isTyping" class="flex items-center justify-center py-12">
          <div class="text-center">
            <Loader2 class="h-12 w-12 animate-spin mx-auto text-primary" />
            <div class="mt-4 text-muted-foreground">Loading...</div>
          </div>
        </div>

        <!-- Backend Error -->
        <Card v-if="backendError" class="border-destructive">
          <CardContent class="p-6">
            <div class="flex items-center gap-3">
              <AlertTriangle class="h-5 w-5 text-destructive" />
              <div>
                <div class="font-semibold text-destructive">Backend Server Not Available</div>
                <div class="text-sm text-muted-foreground mt-1">{{ backendError }}</div>
                <div class="text-xs text-muted-foreground mt-2">
                  Please start the Django backend server by running:<br>
                  <code class="bg-muted px-2 py-1 rounded">cd backend && python manage.py runserver 8000</code>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- No Search Results Yet -->
        <Card v-else-if="!searchResults && !searchQuery">
          <CardContent class="p-12 text-center">
            <Search class="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <div class="text-xl font-semibold mb-2">Enter a search query</div>
            <div class="text-muted-foreground">Start typing to see live search results, or press Enter to finalize</div>
          </CardContent>
        </Card>

        <!-- Entity Sorted Results -->
        <div v-else-if="searchResults?.results && searchResults.results.length > 0">
          <EntitySortedResults_TPRM
            :search-results="searchResults.results"
            :search-query="searchQuery"
            :search-terms="searchTerms"
            :is-loading="isLoading"
            :page-size="pageSize"
            :current-page="currentPage"
            :selected-modules="activeFilters.module"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />
        </div>

        <!-- No Results -->
        <Card v-else-if="searchResults?.results && searchResults.results.length === 0">
          <CardContent class="p-12 text-center">
            <Search class="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <div class="text-xl font-semibold mb-2">No results found</div>
            <div class="text-muted-foreground">Try adjusting your search terms</div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Analytics Dashboard View -->
    <div v-else-if="currentView === 'analytics'" class="space-y-8">
      <!-- Header with Live Status -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div class="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            @click="handleBackToSearch"
            class="h-10 w-10"
          >
            <ArrowLeft class="h-4 w-4" />
          </Button>
          <div>
            <h1 class="text-3xl font-bold text-foreground">TPRM Analytics Dashboard</h1>
            <p class="text-base text-muted-foreground">Search performance and system metrics</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <Badge :variant="liveStatus.color === 'success' ? 'default' : 'secondary'" class="gap-1">
            <component :is="liveStatus.icon" class="h-3 w-3" />
            {{ liveStatus.text }}
          </Badge>
          <Badge variant="outline" class="text-xs">
            Last Updated: {{ lastUpdateTime }}
          </Badge>
        </div>
      </div>

      <!-- System Health Overview -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-muted-foreground">Avg Response Time</p>
                <p class="text-2xl font-bold">{{ analytics?.search_analytics?.avg_response_time || 0 }}ms</p>
                <Badge :variant="getHealthColor(analytics?.system_health?.search_performance) === 'success' ? 'default' : 'destructive'" class="mt-1">
                  {{ analytics?.system_health?.search_performance || 'warning' }}
                </Badge>
              </div>
              <component :is="getHealthIcon(analytics?.system_health?.search_performance)" 
                         :class="`h-8 w-8 ${getHealthColor(analytics?.system_health?.search_performance) === 'success' ? 'text-green-600' : 'text-orange-600'}`" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-muted-foreground">Searches (24h)</p>
                <p class="text-2xl font-bold">{{ analytics?.search_analytics?.searches_24h || 0 }}</p>
                <Badge :variant="analytics?.system_health?.recent_activity === 'active' ? 'default' : 'secondary'" class="mt-1">
                  {{ analytics?.system_health?.recent_activity || 'active' }}
                </Badge>
              </div>
              <component :is="analytics?.system_health?.recent_activity === 'active' ? Activity : Moon" 
                         :class="`h-8 w-8 ${analytics?.system_health?.recent_activity === 'active' ? 'text-green-600' : 'text-orange-600'}`" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-muted-foreground">Zero Result Rate</p>
                <p class="text-2xl font-bold">{{ analytics?.system_health?.zero_result_rate || 0 }}%</p>
                <Badge :variant="analytics?.system_health?.zero_result_rate > 50 ? 'destructive' : 'default'" class="mt-1">
                  {{ analytics?.system_health?.zero_result_rate > 50 ? 'High' : 'Good' }}
                </Badge>
              </div>
              <component :is="analytics?.system_health?.zero_result_rate > 50 ? 'AlertTriangle' : 'CheckCircle'" 
                         :class="`h-8 w-8 ${analytics?.system_health?.zero_result_rate > 50 ? 'text-red-600' : 'text-green-600'}`" />
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Search Analytics -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>Search Performance</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                @click="refreshAnalytics"
                :disabled="isAnalyticsLoading"
              >
                <RefreshCw :class="`h-4 w-4 ${isAnalyticsLoading ? 'animate-spin' : ''}`" />
              </Button>
            </div>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Total Searches</span>
              <Badge variant="secondary">{{ analytics?.search_analytics?.total_searches || 0 }}</Badge>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Searches (7 days)</span>
              <Badge variant="secondary">{{ analytics?.search_analytics?.searches_7d || 0 }}</Badge>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Zero Result Searches</span>
              <Badge variant="destructive">{{ analytics?.search_analytics?.zero_result_searches || 0 }}</Badge>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Zero Result Searches (24h)</span>
              <Badge variant="destructive">{{ analytics?.search_analytics?.zero_result_searches_24h || 0 }}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Index Activity (24h)</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Recent Updates</span>
              <Badge variant="default">{{ analytics?.search_index?.recent_updates_24h || 0 }}</Badge>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Avg Response Time (24h)</span>
              <Badge variant="secondary">{{ analytics?.search_analytics?.avg_response_time_24h || 0 }}ms</Badge>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Search Activity</span>
              <Badge :variant="analytics?.system_health?.recent_activity === 'active' ? 'default' : 'secondary'">
                {{ analytics?.system_health?.recent_activity || 'active' }}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Popular Searches and Live Activity -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Popular Searches (7 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div v-if="analytics?.search_analytics?.popular_searches?.length" class="space-y-3">
              <div 
                v-for="(search, index) in analytics.search_analytics.popular_searches.slice(0, 5)" 
                :key="index"
                class="flex justify-between items-center p-3 border rounded-lg"
              >
                <span class="text-sm font-medium">{{ search.query }}</span>
                <Badge variant="secondary">{{ search.count }}</Badge>
              </div>
            </div>
            <div v-else class="text-center py-8 text-muted-foreground">
              No search data available
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>Live Activity</CardTitle>
              <Badge :variant="liveUpdates?.is_active ? 'default' : 'secondary'">
                {{ liveUpdates?.is_active ? 'Active' : 'Quiet' }}
              </Badge>
            </div>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Recent Searches (5min)</span>
              <Badge variant="secondary">{{ liveUpdates?.recent_searches || 0 }}</Badge>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium">Index Updates (5min)</span>
              <Badge variant="default">{{ liveUpdates?.recent_index_updates || 0 }}</Badge>
            </div>
            <div v-if="liveUpdates?.latest_queries?.length" class="space-y-2">
              <div class="text-sm font-semibold">Latest Queries:</div>
              <div 
                v-for="query in liveUpdates.latest_queries.slice(0, 3)" 
                :key="query.created_at"
                class="text-xs text-muted-foreground p-2 bg-muted rounded"
              >
                "{{ query.query }}" ({{ query.results_count }} results)
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Loading State -->
      <div v-if="isAnalyticsLoading" class="flex items-center justify-center py-12">
        <div class="text-center">
          <Loader2 class="h-12 w-12 animate-spin mx-auto text-primary" />
          <div class="mt-4 text-muted-foreground">Loading analytics...</div>
        </div>
      </div>

      <!-- Error State -->
      <Card v-if="analyticsError" class="border-destructive">
        <CardContent class="p-6">
          <div class="flex items-center gap-3">
            <AlertTriangle class="h-5 w-5 text-destructive" />
            <div>
              <div class="font-semibold text-destructive">Failed to Load Analytics</div>
              <div class="text-sm text-muted-foreground mt-1">{{ analyticsError }}</div>
              <Button
                variant="outline"
                class="mt-3"
                @click="refreshAnalytics"
              >
                Retry
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchAPI } from '@/services/globalsearch_api'
import EntitySortedResults_TPRM from '@/components_globalsearch/EntitySortedResults_TPRM.vue'
import SearchHistory_TPRM from '@/components_globalsearch/SearchHistory_TPRM.vue'
import SearchFilters_TPRM from '@/components_globalsearch/SearchFilters_TPRM.vue'

// TPRM UI Components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

// Icons
import { 
  Search, 
  BarChart3, 
  ArrowLeft, 
  Loader2, 
  AlertTriangle, 
  Activity, 
  CheckCircle, 
  RefreshCw,
  Moon
} from 'lucide-vue-next'

// Debounce function for live search
function debounce(func, wait) {
  let timeout = null
  
  const debounced = (...args) => {
    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(() => func(...args), wait)
  }
  
  debounced.cancel = () => {
    if (timeout) {
      clearTimeout(timeout)
      timeout = null
    }
  }
  
  return debounced
}

const route = useRoute()
const router = useRouter()

// View state management
const currentView = ref('search') // 'search' or 'analytics'

// Reactive data
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(1000)  // Increased default page size to show more results
const activeFilters = ref({
  module: [],
  status: [],
  category: [],
  risk_level: []
})

// Analytics data
const analytics = ref(null)
const liveUpdates = ref(null)
const isAnalyticsLoading = ref(false)
const analyticsError = ref(null)
const lastUpdateTime = ref('')
const updateInterval = ref(null)
const liveUpdateInterval = ref(null)

// Computed
const totalPages = computed(() => {
  if (!searchResults.value?.total) return 0
  return Math.ceil(searchResults.value.total / pageSize.value)
})

const searchTerms = computed(() => {
  return searchQuery.value ? searchQuery.value.split(' ') : []
})

// Analytics computed properties
const liveStatus = computed(() => {
  if (liveUpdates.value?.is_active) {
    return {
      text: 'Live',
      color: 'success',
      icon: 'Activity'
    }
  } else if (analytics.value) {
    return {
      text: 'Connected',
      color: 'info',
      icon: 'CheckCircle'
    }
  } else {
    return {
      text: 'Disconnected',
      color: 'error',
      icon: 'AlertTriangle'
    }
  }
})

// Search state
const searchResults = ref(null)
const isLoading = ref(false)
const isTyping = ref(false)
const backendError = ref(null)
const lastSearchTime = ref(0)
const SEARCH_COOLDOWN = 300  // Reduced for better responsiveness
const TYPING_DEBOUNCE = 300  // Faster response for live search

// Search history component ref
const searchHistoryRef = ref(null)

// Methods
const performSearch = async (isNewSearch = true, isLiveSearch = false) => {
  const now = Date.now()
  if (now - lastSearchTime.value < SEARCH_COOLDOWN && isLiveSearch) {
    console.log('Live search rate limited, skipping...')
    return
  }
  lastSearchTime.value = now
  
  if (isLiveSearch) {
    isTyping.value = true
  } else {
    isLoading.value = true
  }
  backendError.value = null
  
  if (isNewSearch) {
    currentPage.value = 1
  }
  
  try {
    const searchParamsWithFinalized = {
      q: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value,
      is_finalized: !isLiveSearch, // Live searches are not finalized
      module: activeFilters.value.module,
      status: activeFilters.value.status,
      category: activeFilters.value.category,
      risk_level: activeFilters.value.risk_level
    }
    
    console.log('Search params:', searchParamsWithFinalized)
    const response = await searchAPI.search(searchParamsWithFinalized)
    console.log('Search response:', response)
   
    if (response.results) {
      searchResults.value = response
    } else if (response.grouped_results) {
      const flatResults = []
      Object.values(response.grouped_results).forEach((results) => {
        flatResults.push(...results)
      })
      searchResults.value = {
        ...response,
        results: flatResults
      }
    } else {
      searchResults.value = {
        total: 0,
        page: 1,
        page_size: pageSize.value,
        results: [],
        query_time: 0,
        query: searchQuery.value
      }
    }
    
    if (response.error) {
      backendError.value = response.error
    }
    
    // Refresh search history only after finalized searches (not live searches)
    if (!isLiveSearch && searchHistoryRef.value) {
      console.log('Refreshing search history after finalized search...')
      await searchHistoryRef.value.refreshSearchHistory()
    }
  } catch (error) {
    console.error('Search failed:', error)
    searchResults.value = {
      total: 0,
      page: 1,
      page_size: pageSize.value,
      results: [],
      query_time: 0,
      query: searchQuery.value
    }
    backendError.value = 'Failed to connect to the search server. Please try again.'
  } finally {
    if (isLiveSearch) {
      isTyping.value = false
    } else {
      isLoading.value = false
    }
  }
}

const handleSearchInput = () => {
  if (searchQuery.value.trim()) {
    // Trigger live search as user types
    debouncedLiveSearch()
  } else {
    // Clear results if search input is empty
    searchResults.value = null
    isTyping.value = false
  }
}

const finalizeSearch = async () => {
  debouncedLiveSearch.cancel()  // Cancel any pending live search
  isTyping.value = false
  
  if (searchQuery.value.trim()) {
    await performSearch(true, false)  // Finalized search
  }
}

const handlePageChange = async (page) => {
  currentPage.value = page
  await performSearch(false, false)  // Not a new search, not live search
}

const handlePageSizeChange = async () => {
  currentPage.value = 1
  await performSearch(true, false)  // New search, not live search
}

const debouncedLiveSearch = debounce(() => {
  performSearch(true, true)  // New search, live search
}, TYPING_DEBOUNCE)

const handleHistorySelect = (query) => {
  searchQuery.value = query
  finalizeSearch()
}

const handleFilterChange = () => {
  if (searchQuery.value.trim()) {
    // Trigger live search when filters change
    debouncedLiveSearch()
  }
}

const handleViewAnalytics = async () => {
  currentView.value = 'analytics'
  await loadAnalytics()
  await loadLiveUpdates()
  startAutoRefresh()
}

const handleBackToSearch = () => {
  currentView.value = 'search'
  stopAutoRefresh()
}

// Analytics methods
const getHealthColor = (status) => {
  switch (status) {
    case 'healthy':
    case 'good':
    case 'active':
      return 'success'
    case 'warning':
    case 'slow':
      return 'warning'
    case 'critical':
    case 'poor':
    case 'inactive':
      return 'error'
    default:
      return 'grey'
  }
}

const getHealthIcon = (status) => {
  switch (status) {
    case 'healthy':
    case 'good':
    case 'active':
      return 'CheckCircle'
    case 'warning':
    case 'slow':
      return 'AlertTriangle'
    case 'critical':
    case 'poor':
    case 'inactive':
      return 'AlertTriangle'
    default:
      return 'AlertTriangle'
  }
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const loadAnalytics = async () => {
  try {
    isAnalyticsLoading.value = true
    analyticsError.value = null
    
    const response = await searchAPI.getDashboardAnalytics()
    analytics.value = response
    lastUpdateTime.value = formatTime(response.timestamp)
    
  } catch (err) {
    console.error('Failed to load analytics:', err)
    analyticsError.value = err.message || 'Failed to load analytics data'
  } finally {
    isAnalyticsLoading.value = false
  }
}

const loadLiveUpdates = async () => {
  try {
    const response = await searchAPI.getLiveUpdates()
    liveUpdates.value = response
  } catch (err) {
    console.error('Failed to load live updates:', err)
  }
}

const refreshAnalytics = () => {
  loadAnalytics()
}

const startAutoRefresh = () => {
  updateInterval.value = setInterval(() => {
    loadAnalytics()
  }, 30000)
  
  liveUpdateInterval.value = setInterval(() => {
    loadLiveUpdates()
  }, 10000)
}

const stopAutoRefresh = () => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
    updateInterval.value = null
  }
  if (liveUpdateInterval.value) {
    clearInterval(liveUpdateInterval.value)
    liveUpdateInterval.value = null
  }
}

// Watch for route changes
watch(() => route.query.q, (newQuery) => {
  if (newQuery && typeof newQuery === 'string' && newQuery !== searchQuery.value) {
    searchQuery.value = newQuery
    // Use nextTick to avoid recursive updates
    nextTick(() => {
      finalizeSearch()
    })
  }
}, { immediate: false })

// Initialize from route
onMounted(() => {
  if (route.query.q && typeof route.query.q === 'string') {
    searchQuery.value = route.query.q
    finalizeSearch()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>
