import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGlobalSearchStore = defineStore('globalsearch', () => {
  // State
  const searchQuery = ref('')
  const searchResults = ref(null)
  const isLoading = ref(false)
  const selectedModules = ref([])
  const selectedStatuses = ref([])
  const dateRange = ref(null)
  const sortBy = ref('relevance')
  const currentPage = ref(1)
  const pageSize = ref(10)

  // Getters
  const hasActiveFilters = computed(() => {
    return selectedModules.value.length > 0 ||
           selectedStatuses.value.length > 0 ||
           dateRange.value !== null
  })

  const totalPages = computed(() => {
    if (!searchResults.value?.total_results) return 0
    return Math.ceil(searchResults.value.total_results / pageSize.value)
  })

  const searchParams = computed(() => ({
    query: searchQuery.value,
    modules: selectedModules.value,
    statuses: selectedStatuses.value,
    date_from: dateRange.value?.start,
    date_to: dateRange.value?.end,
    sort_by: sortBy.value,
    page: currentPage.value,
    page_size: pageSize.value
  }))

  // Actions
  const setSearchQuery = (query) => {
    searchQuery.value = query
  }

  const setSearchResults = (results) => {
    searchResults.value = results
  }

  const setLoading = (loading) => {
    isLoading.value = loading
  }

  const setSelectedModules = (modules) => {
    selectedModules.value = modules
  }

  const setSelectedStatuses = (statuses) => {
    selectedStatuses.value = statuses
  }

  const setDateRange = (range) => {
    dateRange.value = range
  }

  const setSortBy = (sort) => {
    sortBy.value = sort
  }

  const setCurrentPage = (page) => {
    currentPage.value = page
  }

  const clearFilters = () => {
    selectedModules.value = []
    selectedStatuses.value = []
    dateRange.value = null
  }

  const resetSearch = () => {
    searchQuery.value = ''
    searchResults.value = null
    isLoading.value = false
    clearFilters()
    sortBy.value = 'relevance'
    currentPage.value = 1
  }

  return {
    // State
    searchQuery,
    searchResults,
    isLoading,
    selectedModules,
    selectedStatuses,
    dateRange,
    sortBy,
    currentPage,
    pageSize,

    // Getters
    hasActiveFilters,
    totalPages,
    searchParams,

    // Actions
    setSearchQuery,
    setSearchResults,
    setLoading,
    setSelectedModules,
    setSelectedStatuses,
    setDateRange,
    setSortBy,
    setCurrentPage,
    clearFilters,
    resetSearch
  }
})
