<template>
  <div class="relative">
    <!-- Dev Phases Button -->
    <button
      type="button"
      @click="toggleDropdown"
      class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-purple-100 border border-purple-200 rounded-md hover:bg-purple-200 transition-colors"
    >
      <!-- Construction Icon -->
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#F59E0B"/>
        <path d="M2 17L12 22L22 17" stroke="#1F2937" stroke-width="2" fill="none"/>
        <path d="M2 12L12 17L22 12" stroke="#1F2937" stroke-width="2" fill="none"/>
      </svg>
      
      <!-- Chevron Left -->
      <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      
      <span>RFP Workflow</span>
      
      <!-- Chevron Right -->
      <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>

    <!-- Dropdown Menu -->
    <div
      v-if="isOpen"
      class="absolute top-full left-0 mt-1 w-80 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-[600px] overflow-y-auto"
    >
      <div class="py-2">
        <!-- Header -->
        <div class="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-100 bg-gray-50">
          RFP Workflow Navigation
        </div>
        
        <!-- Categorized Phases with Expandable Categories -->
        <div class="mt-2">
          <div v-for="category in categorizedPhases" :key="category.id" class="mb-1">
            <!-- Category Header - Expandable -->
            <button
              type="button"
              @click.stop.prevent="toggleCategory(category.id)"
              class="w-full flex items-center justify-between px-3 py-2.5 text-sm font-semibold text-gray-700 bg-gray-50 hover:bg-gray-100 border-b border-gray-200 transition-colors"
            >
              <div class="flex items-center gap-2">
                <component :is="category.icon" class="h-4 w-4 text-gray-600" />
                <span class="text-xs uppercase tracking-wide">{{ category.name }}</span>
              </div>
              <!-- Chevron Icon -->
              <svg 
                :class="['h-3.5 w-3.5 text-gray-500 transition-transform duration-200', expandedCategories.includes(category.id) ? 'rotate-180' : '']" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            <!-- Category Description -->
            <div class="px-3 py-1.5 bg-gray-50 border-b border-gray-200">
              <p class="text-xs text-gray-500">{{ category.description }}</p>
            </div>
            
            <!-- Category Items - Collapsible -->
            <div v-if="expandedCategories.includes(category.id)" class="bg-white">
              <button
                v-for="phase in category.phases"
                :key="phase.routeName"
                type="button"
                @click.stop.prevent="navigateTo(phase.routeName)"
                :disabled="!phase.available"
                :class="[
                  'block w-full text-left px-6 py-2.5 text-sm transition-colors border-b border-gray-100 last:border-b-0',
                  phase.available 
                    ? 'text-gray-700 hover:bg-purple-50 hover:text-purple-900 cursor-pointer' 
                    : 'text-gray-400 cursor-not-allowed opacity-50'
                ]"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2.5">
                    <span class="inline-flex items-center justify-center w-6 h-6 text-xs font-bold rounded-full bg-purple-100 text-purple-700">
                      {{ phase.number }}
                    </span>
                    <span class="font-medium">{{ phase.name }}</span>
                  </div>
                  <span v-if="!phase.available" class="text-xs text-gray-400">(Soon)</span>
                </div>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Quick Links -->
        <div class="border-t border-gray-200 mt-2 pt-2">
          <button
            type="button"
            @click.stop.prevent="navigateTo('RFPWorkflow')"
            class="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors border-b border-gray-100"
          >
            <div class="flex items-center gap-2">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span class="font-medium">Workflow Overview</span>
            </div>
          </button>
          <button
            type="button"
            @click.stop.prevent="navigateTo('Dashboard')"
            class="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          >
            <div class="flex items-center gap-2">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span class="font-medium">Dashboard</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const isOpen = ref(false)
const expandedCategories = ref<string[]>(['planning', 'vendor-engagement', 'evaluation', 'finalization'])

// Icon components as render functions
const FileTextIcon = () => h('svg', {
  class: 'h-4 w-4',
  fill: 'none',
  viewBox: '0 0 24 24',
  stroke: 'currentColor'
}, [
  h('path', {
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    'stroke-width': '2',
    d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
  })
])

const UsersIcon = () => h('svg', {
  class: 'h-4 w-4',
  fill: 'none',
  viewBox: '0 0 24 24',
  stroke: 'currentColor'
}, [
  h('path', {
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    'stroke-width': '2',
    d: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z'
  })
])

const ClipboardCheckIcon = () => h('svg', {
  class: 'h-4 w-4',
  fill: 'none',
  viewBox: '0 0 24 24',
  stroke: 'currentColor'
}, [
  h('path', {
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    'stroke-width': '2',
    d: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
  })
])

const CheckCircleIcon = () => h('svg', {
  class: 'h-4 w-4',
  fill: 'none',
  viewBox: '0 0 24 24',
  stroke: 'currentColor'
}, [
  h('path', {
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    'stroke-width': '2',
    d: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
  })
])

// Categorized RFP workflow phases
const categorizedPhases = [
  {
    id: 'planning',
    name: 'Planning & Setup',
    description: 'Initial planning and approval stages',
    icon: FileTextIcon,
    phases: [
      { number: 1, name: 'Creation', routeName: 'RFPCreation', available: true },
      { number: 2, name: 'Approval', routeName: 'RFPApproval', available: true }
    ]
  },
  {
    id: 'vendor-engagement',
    name: 'Vendor Engagement',
    description: 'Vendor outreach and response collection',
    icon: UsersIcon,
    phases: [
      { number: 3, name: 'Vendor Selection', routeName: 'RFPVendorSelection', available: true },
      { number: 4, name: 'URL Generation', routeName: 'RFPUrlGeneration', available: true }
    ]
  },
  {
    id: 'evaluation',
    name: 'Evaluation & Analysis',
    description: 'Response evaluation and decision making',
    icon: ClipboardCheckIcon,
    phases: [
      { number: 6, name: 'Evaluation', routeName: 'RFPEvaluation', available: true },
      { number: 7, name: 'Comparison', routeName: 'RFPComparison', available: true },
      { number: 8, name: 'Consensus', routeName: 'RFPConsensus', available: true }
    ]
  },
  {
    id: 'finalization',
    name: 'Finalization',
    description: 'Award and vendor selection',
    icon: CheckCircleIcon,
    phases: [
      { number: 9, name: 'Award', routeName: 'RFPAward', available: true }
    ]
  }
]

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const toggleCategory = (categoryId: string) => {
  const index = expandedCategories.value.indexOf(categoryId)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

const navigateTo = (routeName: string) => {
  console.log('Navigating to:', routeName)
  
  // Route mapping for navigation
  const routeMap: { [key: string]: string } = {
    'RFPCreation': '/rfp-creation',
    'RFPApproval': '/rfp-approval',
    'RFPVendorSelection': '/rfp-vendor-selection',
    'RFPUrlGeneration': '/rfp-url-generation',
    'VendorPortal': '/vendor-portal',
    'RFPEvaluation': '/rfp-evaluation',
    'RFPComparison': '/rfp-comparison',
    'RFPConsensus': '/rfp-consensus',
    'RFPAward': '/rfp-award',
    'RFPWorkflow': '/rfp-workflow',
    'Dashboard': '/rfp-dashboard'
  }
  
  const targetPath = routeMap[routeName]
  
  if (!targetPath) {
    console.warn(`No route mapping found for ${routeName}`)
    closeDropdown()
    return false
  }
  
  // Check if the route is available by searching through all categories
  // This is only for validation, not blocking navigation
  let foundPhase = null
  for (const category of categorizedPhases) {
    const phase = category.phases.find(p => p.routeName === routeName)
    if (phase) {
      foundPhase = phase
      break
    }
  }
  
  // Check if route is in quick links (RFPWorkflow, Dashboard)
  const isQuickLink = routeName === 'RFPWorkflow' || routeName === 'Dashboard'
  
  if (!foundPhase && !isQuickLink) {
    console.warn(`Route ${routeName} is not available`)
    closeDropdown()
    return false
  }
  
  console.log('Target path:', targetPath)
  console.log('Current route:', route.path)
  
  // Close dropdown first
  closeDropdown()
  
  // Navigate using router - use replace to avoid adding to history
  router.push(targetPath).catch((error) => {
    console.error(`Navigation error for ${routeName}:`, error)
    // Fallback to window location if router fails
    window.location.href = targetPath
  })
  
  return false
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Ensure dropdown appears above other elements */
.relative {
  position: relative;
}

/* Smooth transitions */
.transition-colors {
  transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
}

/* Hover effects */
.hover\:bg-purple-200:hover {
  background-color: rgb(221 214 254);
}

.hover\:bg-gray-50:hover {
  background-color: rgb(249 250 251);
}

.hover\:text-gray-900:hover {
  color: rgb(17 24 39);
}

.hover\:text-gray-700:hover {
  color: rgb(55 65 81);
}
</style>
