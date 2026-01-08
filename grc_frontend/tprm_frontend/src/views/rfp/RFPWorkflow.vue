<template>
  <div class="space-y-6">
    <div class="md:flex md:items-center md:justify-between">
      <div class="flex-1 min-w-0">
        <h2 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          RFP Workflow
        </h2>
        <p class="mt-1 text-sm text-gray-500">
          Manage your RFP process from creation to award
        </p>
      </div>
    </div>
    
    <!-- RFP Workflow Progress -->
    <RFPWorkflowProgress 
      :current-phase="currentPhase"
      :completed-phases="completedPhases"
      @phase-click="handlePhaseClick"
      @view-click="handleViewClick"
      @start-click="handleStartClick"
    />

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      <Card v-for="action in quickActions" :key="action.name">
        <div class="text-center">
          <component :is="action.icon" class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900">{{ action.name }}</h3>
          <p class="mt-1 text-sm text-gray-500">{{ action.description }}</p>
          <div class="mt-6">
            <Button variant="outline" size="sm" @click="navigateToStep(action.route)">
              {{ action.buttonText }}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components_rfp/Card.vue'
import Button from '@/components_rfp/Button.vue'
import RFPWorkflowProgress from '@/components_rfp/ui/RFPWorkflowProgress.vue'

const router = useRouter()

// RFP Workflow state - determine current phase from URL
const getCurrentPhase = () => {
  const path = window.location.pathname
  
  // Map new route names to phase identifiers
  const routeMap: { [key: string]: string } = {
    '/rfp-creation': 'phase-1',
    '/rfp-approval': 'phase-2',
    '/rfp-vendor-selection': 'phase-3',
    '/rfp-url-generation': 'phase-4',
    '/rfp-evaluation': 'phase-6',
    '/rfp-comparison': 'phase-7',
    '/rfp-consensus': 'phase-8',
    '/rfp-award': 'phase-8', // Award is now combined with Consensus
  }
  
  return routeMap[path] || 'phase-1'
}

const currentPhase = ref(getCurrentPhase())
const completedPhases = ref<string[]>([])

const quickActions = ref([
  {
    name: 'Create New RFP',
    description: 'Start a new RFP process',
    buttonText: 'Create',
    route: '/rfp-creation',
    icon: markRaw({
      template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>'
    })
  }
])

const navigateToStep = (route: string) => {
  router.push(route)
}

// RFP Workflow Navigation Handlers
const handlePhaseClick = (phase: any) => {
  // Navigate to the phase route using Vue Router
  if (phase.route) {
    console.log('Navigating to:', phase.route)
    router.push(phase.route)
  }
}

const handleViewClick = (phase: any) => {
  // Handle view action for completed phases
  console.log('Viewing phase:', phase.id)
  // Navigate to view mode for the phase
  if (phase.route) {
    router.push(phase.route)
  }
}

const handleStartClick = (phase: any) => {
  // Handle start action for active phases
  console.log('Starting phase:', phase.id)
  // Navigate to the phase to start working on it
  if (phase.route) {
    router.push(phase.route)
  }
}
</script>

<style scoped>
/* Additional workflow-specific styles can be added here */
</style>
