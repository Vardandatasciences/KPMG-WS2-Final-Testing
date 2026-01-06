<template>
  <div class="rfp-workflow-progress">
    <div class="workflow-container">
      <div class="flex items-center justify-between">
        <div
          v-for="(phase, index) in phases"
          :key="phase.id"
          class="workflow-step"
          :class="{ 'cursor-pointer': phase.status !== 'pending' }"
          @click="handlePhaseClick(phase)"
        >
          <!-- Step Circle -->
          <div class="step-indicator">
            <div
              :class="getStepCircleClasses(phase)"
              class="step-circle"
            >
              <Icons
                :name="phase.icon"
                :class="getIconClasses(phase)"
              />
              
              <!-- Completion Checkmark Overlay -->
              <div
                v-if="phase.status === 'completed'"
                class="completion-badge"
              >
                <Icons name="check" class="w-3 h-3 text-white" />
              </div>
            </div>
            
            <!-- Step Content -->
            <div class="step-content">
              <h3 :class="getTitleClasses(phase)" class="step-title">
                {{ phase.title }}
              </h3>
              <p :class="getDescriptionClasses(phase)" class="step-description">
                {{ phase.description }}
              </p>
              <div class="step-actions">
                <!-- Action Button -->
                <Button
                  v-if="phase.status === 'completed'"
                  variant="outline"
                  size="sm"
                  @click.stop="handleViewClick(phase)"
                  class="action-btn"
                >
                  View
                </Button>
                <Button
                  v-else-if="phase.status === 'active'"
                  size="sm"
                  @click.stop="handleStartClick(phase)"
                  class="action-btn start-btn"
                >
                  Start
                </Button>
                <span
                  v-else
                  class="pending-text"
                >
                  Pending
                </span>
              </div>
            </div>
          </div>

          <!-- Connecting Line -->
          <div
            v-if="index < phases.length - 1"
            :class="getLineClasses(phase, phases[index + 1])"
            class="connecting-line"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'
import Icons from './Icons.vue'
import Button from './Button.vue'

interface RFPPhase {
  id: string
  title: string
  description: string
  status: 'completed' | 'active' | 'pending'
  icon: string
  route?: string
}

interface Props {
  currentPhase?: string
  completedPhases?: string[]
  className?: string
}

interface Emits {
  (e: 'phaseClick', phase: RFPPhase): void
  (e: 'viewClick', phase: RFPPhase): void
  (e: 'startClick', phase: RFPPhase): void
}

const props = withDefaults(defineProps<Props>(), {
  currentPhase: 'phase-1',
  completedPhases: () => [],
  className: ''
})

const emit = defineEmits<Emits>()

// Complete RFP Workflow Phases
const phases = computed<RFPPhase[]>(() => [
  {
    id: 'phase-1',
    title: 'RFP Creation',
    description: 'Define requirements and create RFP document',
    status: props.completedPhases.includes('phase-1') ? 'completed' : 
            (props.currentPhase === 'phase-1' ? 'active' : 'pending'),
    icon: 'file-text2',
    route: '/rfp-creation'
  },
  {
    id: 'phase-2',
    title: 'Approval Process',
    description: 'Get internal approval for RFP',
    status: props.completedPhases.includes('phase-2') ? 'completed' : 
            (props.currentPhase === 'phase-2' ? 'active' : 'pending'),
    icon: 'check-circle',
    route: '/rfp-approval'
  },
  {
    id: 'phase-3',
    title: 'Vendor Selection',
    description: 'Select vendors to invite',
    status: props.completedPhases.includes('phase-3') ? 'completed' : 
            (props.currentPhase === 'phase-3' ? 'active' : 'pending'),
    icon: 'users',
    route: '/rfp-vendor-selection'
  },
  {
    id: 'phase-4',
    title: 'URL Generation',
    description: 'Generate unique URLs for vendors',
    status: props.completedPhases.includes('phase-4') ? 'completed' : 
            (props.currentPhase === 'phase-4' ? 'active' : 'pending'),
    icon: 'target',
    route: '/rfp-url-generation'
  },

  {
    id: 'phase-6',
    title: 'Evaluation',
    description: 'Evaluate vendor proposals',
    status: props.completedPhases.includes('phase-6') ? 'completed' : 
            (props.currentPhase === 'phase-6' ? 'active' : 'pending'),
    icon: 'award',
    route: '/rfp-evaluation'
  },
  {
    id: 'phase-7',
    title: 'Comparison',
    description: 'Compare vendor proposals',
    status: props.completedPhases.includes('phase-7') ? 'completed' : 
            (props.currentPhase === 'phase-7' ? 'active' : 'pending'),
    icon: 'target',
    route: '/rfp-comparison'
  },
  {
    id: 'phase-8',
    title: 'Consensus & Award',
    description: 'Reach consensus and award contract',
    status: (props.completedPhases.includes('phase-8') || props.completedPhases.includes('phase-9')) ? 'completed' : 
            (props.currentPhase === 'phase-8' || props.currentPhase === 'phase-9' ? 'active' : 'pending'),
    icon: 'target',
    route: '/rfp-consensus'
  }
])

const getStepCircleClasses = (phase: RFPPhase) => {
  const baseClasses = 'w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 border-2'
  
  if (phase.status === 'completed') {
    return rfpCn(baseClasses, 'bg-green-500 border-green-500 text-white shadow-lg shadow-green-200')
  } else if (phase.status === 'active') {
    return rfpCn(baseClasses, 'bg-blue-500 border-blue-500 text-white shadow-lg shadow-blue-200 animate-pulse')
  }
  
  return rfpCn(baseClasses, 'bg-white border-gray-300 text-gray-400')
}

const getIconClasses = (phase: RFPPhase) => {
  const baseClasses = 'w-5 h-5'
  
  if (phase.status === 'completed' || phase.status === 'active') {
    return rfpCn(baseClasses, 'text-white')
  }
  
  return rfpCn(baseClasses, 'text-gray-400')
}

const getTitleClasses = (phase: RFPPhase) => {
  const baseClasses = 'font-semibold text-base'
  
  if (phase.status === 'completed') {
    return rfpCn(baseClasses, 'text-green-700')
  } else if (phase.status === 'active') {
    return rfpCn(baseClasses, 'text-blue-700')
  }
  
  return rfpCn(baseClasses, 'text-gray-600')
}

const getDescriptionClasses = (phase: RFPPhase) => {
  const baseClasses = 'text-sm'
  
  if (phase.status === 'completed') {
    return rfpCn(baseClasses, 'text-green-600')
  } else if (phase.status === 'active') {
    return rfpCn(baseClasses, 'text-blue-600')
  }
  
  return rfpCn(baseClasses, 'text-gray-500')
}

const getLineClasses = (currentPhase: RFPPhase, nextPhase: RFPPhase) => {
  const baseClasses = 'h-0.5 w-8 transition-all duration-300'
  
  if (currentPhase.status === 'completed') {
    return rfpCn(baseClasses, 'bg-green-500')
  } else if (currentPhase.status === 'active') {
    return rfpCn(baseClasses, 'bg-blue-500')
  }
  
  return rfpCn(baseClasses, 'bg-gray-300')
}

const handlePhaseClick = (phase: RFPPhase) => {
  if (phase.status !== 'pending' && phase.route) {
    // Navigate directly to the phase page for MPA setup
    window.location.href = phase.route
  }
}

const handleViewClick = (phase: RFPPhase) => {
  if (phase.route) {
    window.location.href = phase.route
  }
}

const handleStartClick = (phase: RFPPhase) => {
  if (phase.route) {
    window.location.href = phase.route
  }
}
</script>

<style scoped>
.rfp-workflow-progress {
  @apply w-full bg-white rounded-lg border border-gray-200 shadow-sm;
}

.workflow-container {
  @apply p-6;
}

.workflow-step {
  @apply flex flex-col items-center relative transition-all duration-200;
}

.workflow-step:hover {
  @apply transform scale-105;
}

.step-indicator {
  @apply flex flex-col items-center relative;
}

.step-circle {
  @apply relative z-10 mb-3;
}

.completion-badge {
  @apply absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center;
}

.connecting-line {
  @apply absolute top-6 left-full transform -translate-y-1/2;
}

.step-content {
  @apply text-center max-w-24;
}

.step-title {
  @apply m-0 text-sm font-semibold mb-1 leading-tight;
}

.step-actions {
  @apply mt-2;
}

.action-btn {
  @apply text-xs px-2 py-1;
}

.start-btn {
  @apply bg-blue-500 hover:bg-blue-600 text-white;
}

.pending-text {
  @apply text-xs text-gray-400 font-medium;
}

.step-description {
  @apply m-0 text-xs leading-tight mb-2;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
