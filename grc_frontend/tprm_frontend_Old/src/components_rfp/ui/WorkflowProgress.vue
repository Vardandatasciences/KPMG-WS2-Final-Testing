<template>
  <div class="workflow-progress">
    <div class="flex items-center justify-center">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="flex items-center"
        :class="{ 'flex-1': index < steps.length - 1 }"
      >
        <!-- Step Circle -->
        <div class="flex flex-col items-center relative">
          <div
            :class="getStepCircleClasses(step, index)"
            class="step-circle relative z-10"
          >
            <!-- Icon -->
            <Icons
              :name="step.icon"
              :class="getIconClasses(step, index)"
            />
            
            <!-- Completion Checkmark Overlay -->
            <div
              v-if="step.status === 'completed'"
              class="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center"
            >
              <Icons name="check" class="w-3 h-3 text-white" />
            </div>
          </div>
          
          <!-- Step Label -->
          <span
            :class="getLabelClasses(step, index)"
            class="step-label mt-3"
          >
            {{ step.label }}
          </span>
          
          <!-- Step Description -->
          <span
            v-if="step.description"
            :class="getDescriptionClasses(step, index)"
            class="step-description mt-1"
          >
            {{ step.description }}
          </span>
        </div>

        <!-- Connecting Line -->
        <div
          v-if="index < steps.length - 1"
          :class="getLineClasses(index)"
          class="connecting-line"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'
import Icons from './Icons.vue'

interface WorkflowStep {
  id: string
  label: string
  description?: string
  status: 'completed' | 'active' | 'pending'
  icon: string
}

interface Props {
  steps: WorkflowStep[]
  className?: string
}

const props = defineProps<Props>()

const getStepCircleClasses = (step: WorkflowStep, index: number) => {
  const baseClasses = 'w-16 h-16 rounded-full flex items-center justify-center transition-all duration-500 shadow-lg border-2'
  
  if (step.status === 'completed') {
    return rfpCn(baseClasses, 'bg-gradient-to-br from-green-500 to-green-600 border-green-500 text-white shadow-green-200')
  } else if (step.status === 'active') {
    return rfpCn(baseClasses, 'bg-gradient-to-br from-blue-500 to-blue-600 border-blue-500 text-white shadow-blue-200 animate-pulse')
  }
  
  return rfpCn(baseClasses, 'bg-white border-gray-300 text-gray-400 shadow-gray-200')
}

const getIconClasses = (step: WorkflowStep, index: number) => {
  const baseClasses = 'w-7 h-7'
  
  if (step.status === 'completed' || step.status === 'active') {
    return rfpCn(baseClasses, 'text-white')
  }
  
  return rfpCn(baseClasses, 'text-gray-400')
}

const getLabelClasses = (step: WorkflowStep, index: number) => {
  const baseClasses = 'text-sm font-semibold text-center tracking-wide'
  
  if (step.status === 'completed') {
    return rfpCn(baseClasses, 'text-green-600')
  } else if (step.status === 'active') {
    return rfpCn(baseClasses, 'text-blue-600')
  }
  
  return rfpCn(baseClasses, 'text-gray-500')
}

const getDescriptionClasses = (step: WorkflowStep, index: number) => {
  const baseClasses = 'text-xs text-center'
  
  if (step.status === 'completed') {
    return rfpCn(baseClasses, 'text-green-500')
  } else if (step.status === 'active') {
    return rfpCn(baseClasses, 'text-blue-500')
  }
  
  return rfpCn(baseClasses, 'text-gray-400')
}

const getLineClasses = (index: number) => {
  const baseClasses = 'h-0.5 flex-1 mx-6 transition-all duration-500 rounded-full'
  
  // Check if current step and next step are both completed/active
  const currentStep = props.steps[index]
  const nextStep = props.steps[index + 1]
  
  if (currentStep.status === 'completed') {
    return rfpCn(baseClasses, 'bg-gradient-to-r from-green-500 to-green-400')
  } else if (currentStep.status === 'active') {
    return rfpCn(baseClasses, 'bg-gradient-to-r from-blue-500 to-gray-300')
  }
  
  return rfpCn(baseClasses, 'bg-gray-200')
}
</script>

<style scoped>
.workflow-progress {
  @apply w-full py-4;
}

.step-circle {
  @apply relative z-10;
}

.step-label {
  @apply max-w-24 leading-tight;
}

.step-description {
  @apply max-w-28 leading-tight;
}

.connecting-line {
  @apply relative;
}

.connecting-line::before {
  content: '';
  @apply absolute top-1/2 left-0 right-0 h-0.5 transform -translate-y-1/2 rounded-full;
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
