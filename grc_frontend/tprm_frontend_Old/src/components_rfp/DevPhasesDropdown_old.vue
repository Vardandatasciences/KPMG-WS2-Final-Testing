<template>
  <div class="relative">
    <!-- Dev Phases Button -->
    <button
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
      
      <span>Dev Phases</span>
      
      <!-- Chevron Right -->
      <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>

    <!-- Dropdown Menu -->
    <div
      v-if="isOpen"
      class="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-50"
    >
      <div class="py-1">
        <div class="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-100">
          RFP Workflow Phases
        </div>
        
        <button
          v-for="phase in phases"
          :key="phase.number"
          @click="navigateTo(phase.routeName)"
          :disabled="!phase.available"
          :class="[
            'block w-full text-left px-3 py-2 text-sm transition-colors',
            phase.available 
              ? 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 cursor-pointer' 
              : 'text-gray-400 cursor-not-allowed opacity-50'
          ]"
        >
          <span class="font-medium">Phase {{ phase.number }}:</span>
          <span class="ml-1">{{ phase.name }}</span>
          <span v-if="!phase.available" class="ml-2 text-xs text-gray-400">(Coming Soon)</span>
        </button>
        
        <div class="border-t border-gray-100 mt-1">
          <button
            @click="navigateTo('RFPWorkflow')"
            class="block w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
          >
            📊 Workflow Overview
          </button>
          <button
            @click="navigateTo('Dashboard')"
            class="block w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
          >
            🏠 Dashboard
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isOpen = ref(false)

// Development phase navigation data
const phases = [
  { number: 1, name: 'Creation', routeName: 'RFPCreation', available: true },
  { number: 2, name: 'Approval', routeName: 'RFPApproval', available: true },
  { number: 3, name: 'Vendor Selection', routeName: 'RFPVendorSelection', available: true },
  { number: 4, name: 'URL Generation', routeName: 'RFPUrlGeneration', available: true },
  { number: 5, name: 'Vendor Portal', routeName: 'VendorPortal', available: true },
  { number: 6, name: 'Evaluation', routeName: 'RFPEvaluation', available: true },
  { number: 7, name: 'Comparison', routeName: 'RFPComparison', available: true },
  { number: 8, name: 'Consensus', routeName: 'RFPConsensus', available: true },
  { number: 9, name: 'Award', routeName: 'RFPAward', available: true },
  { number: 10, name: 'Onboarding', routeName: 'RFPOnboarding', available: true }
]

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const navigateTo = (routeName: string) => {
  // Check if the route is available
  const phase = phases.find(p => p.routeName === routeName)
  if (!phase || !phase.available) {
    console.warn(`Route ${routeName} is not available`)
    closeDropdown()
    return
  }
  
  try {
    router.push({ name: routeName })
    closeDropdown()
  } catch (error) {
    console.error(`Navigation error for ${routeName}:`, error)
    // Fallback to window location if router fails
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
      'RFPOnboarding': '/rfp-onboarding',
      'RFPWorkflow': '/rfp-workflow',
      'Dashboard': '/dashboard'
    }
    
    const fallbackRoute = routeMap[routeName]
    if (fallbackRoute) {
      window.location.href = fallbackRoute
    }
    closeDropdown()
  }
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
