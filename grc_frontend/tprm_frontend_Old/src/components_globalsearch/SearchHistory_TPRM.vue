<template>
  <div class="relative">
    <!-- Trigger Button -->
    <Button 
      variant="outline" 
      @click="toggleHistory"
      class="gap-2"
    >
      <History class="h-4 w-4" />
      Search History
      <Badge v-if="searchHistory.length > 0" variant="secondary" class="ml-1">
        {{ searchHistory.length }}
      </Badge>
    </Button>

    <!-- History Dialog -->
    <Dialog v-model:open="isOpen">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Search History</DialogTitle>
          <DialogDescription>
            Your recent search queries and results
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4">
          <!-- Clear History Button -->
          <div class="flex justify-between items-center">
            <div class="text-sm text-muted-foreground">
              {{ searchHistory.length }} recent searches
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              @click="clearHistory"
              :disabled="searchHistory.length === 0"
            >
              <Trash2 class="h-4 w-4 mr-1" />
              Clear All
            </Button>
          </div>

          <!-- History List -->
          <div v-if="searchHistory.length > 0" class="space-y-3 max-h-96 overflow-y-auto">
            <div 
              v-for="(item, index) in searchHistory" 
              :key="item.id"
              class="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
              @click="selectQuery(item.query)"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <!-- Query -->
                  <div class="font-medium text-foreground mb-1 truncate">
                    {{ item.query }}
                  </div>
                  
                  <!-- Metadata -->
                  <div class="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{{ item.results_count }} results</span>
                    <span>{{ formatDate(item.created_at) }}</span>
                    <span v-if="item.module">{{ getModuleLabel(item.module) }}</span>
                  </div>
                  
                  <!-- Recent Results Preview -->
                  <div v-if="item.recent_results && item.recent_results.length > 0" class="mt-2">
                    <div class="text-xs text-muted-foreground mb-1">Recent results:</div>
                    <div class="space-y-1">
                      <div 
                        v-for="result in item.recent_results.slice(0, 2)" 
                        :key="result.id"
                        class="text-xs text-muted-foreground truncate"
                      >
                        {{ result.title }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Actions -->
                <div class="flex items-center gap-1 ml-2">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    @click.stop="selectQuery(item.query)"
                    class="h-8 w-8 p-0"
                  >
                    <Search class="h-3 w-3" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    @click.stop="removeFromHistory(item.id)"
                    class="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                  >
                    <X class="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-8">
            <History class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <div class="text-lg font-semibold text-foreground mb-2">No search history</div>
            <div class="text-sm text-muted-foreground">
              Your search queries will appear here once you start searching
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <div class="mt-2 text-sm text-muted-foreground">Loading history...</div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="isOpen = false">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Success Message -->
    <div v-if="historyCleared" class="fixed top-4 right-4 z-50">
      <div class="bg-green-50 border border-green-200 rounded-lg p-3 shadow-lg">
        <div class="flex items-center gap-2">
          <CheckCircle class="h-4 w-4 text-green-600" />
          <span class="text-sm text-green-800">Search history cleared</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { searchAPI } from '@/services/globalsearch_api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

// TPRM UI Components
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter 
} from '@/components/ui/dialog'

// Icons
import { 
  History, 
  Search, 
  Trash2, 
  X, 
  CheckCircle 
} from 'lucide-vue-next'

dayjs.extend(relativeTime)

const props = defineProps({
  currentQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select-query'])

// Reactive state
const isOpen = ref(false)
const isLoading = ref(false)
const searchHistory = ref([])
const historyCleared = ref(false)
const page = ref(1)
const hasMore = ref(true)

// Computed
const hasHistory = computed(() => searchHistory.value.length > 0)

// Methods
const toggleHistory = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value && searchHistory.value.length === 0) {
    loadSearchHistory()
  }
}

const selectQuery = (query) => {
  emit('select-query', query)
  isOpen.value = false
}

const loadSearchHistory = async () => {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    const response = await searchAPI.getSearchHistory(page.value, 20)
    
    if (response.results) {
      if (page.value === 1) {
        searchHistory.value = response.results
      } else {
        searchHistory.value.push(...response.results)
      }
      
      hasMore.value = response.next !== null
    }
  } catch (error) {
    console.error('Failed to load search history:', error)
  } finally {
    isLoading.value = false
  }
}

const loadMoreHistory = () => {
  if (hasMore.value && !isLoading.value) {
    page.value++
    loadSearchHistory()
  }
}

const clearHistory = async () => {
  try {
    await searchAPI.clearSearchHistory()
    searchHistory.value = []
    historyCleared.value = true
    
    // Hide success message after 3 seconds
    setTimeout(() => {
      historyCleared.value = false
    }, 3000)
  } catch (error) {
    console.error('Failed to clear search history:', error)
  }
}

const removeFromHistory = async (historyId) => {
  try {
    // Remove from local state immediately for better UX
    searchHistory.value = searchHistory.value.filter(item => item.id !== historyId)
    
    // TODO: Implement API call to remove specific history item
    // await searchAPI.removeFromHistory(historyId)
  } catch (error) {
    console.error('Failed to remove from history:', error)
  }
}

const refreshSearchHistory = async () => {
  page.value = 1
  hasMore.value = true
  await loadSearchHistory()
}

const formatDate = (dateString) => {
  try {
    return dayjs(dateString).fromNow()
  } catch {
    return 'Unknown date'
  }
}

const getModuleLabel = (module) => {
  const labels = {
    contract: 'Contract',
    vendor: 'Vendor',
    rfp: 'RFP',
    sla: 'SLA',
    bcp: 'BCP/DRP'
  }
  return labels[module] || module
}

const generateColor = (str) => {
  const colors = [
    'bg-blue-100 text-blue-800',
    'bg-green-100 text-green-800',
    'bg-purple-100 text-purple-800',
    'bg-orange-100 text-orange-800',
    'bg-pink-100 text-pink-800',
    'bg-indigo-100 text-indigo-800',
    'bg-yellow-100 text-yellow-800',
    'bg-red-100 text-red-800'
  ]
  
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

// Expose methods for parent component
defineExpose({
  refreshSearchHistory,
  clearHistory
})
</script>

<style scoped>
/* Custom scrollbar for history list */
.max-h-96::-webkit-scrollbar {
  width: 6px;
}

.max-h-96::-webkit-scrollbar-track {
  background: transparent;
}

.max-h-96::-webkit-scrollbar-thumb {
  background-color: rgb(var(--muted-foreground) / 0.3);
  border-radius: 3px;
}

.max-h-96::-webkit-scrollbar-thumb:hover {
  background-color: rgb(var(--muted-foreground) / 0.5);
}
</style>
