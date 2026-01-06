<template>
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="translate-x-full opacity-0"
    enter-to-class="translate-x-0 opacity-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="translate-x-0 opacity-100"
    leave-to-class="translate-x-full opacity-0"
  >
    <div
      v-if="toast"
      :class="toastClasses"
      role="alert"
      :aria-live="toast.type === 'error' ? 'assertive' : 'polite'"
    >
      <div class="flex items-start gap-3">
        <!-- Icon -->
        <div :class="iconClasses">
          <component :is="iconComponent" class="h-4 w-4" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div v-if="toast.title" class="font-medium text-sm">
            {{ toast.title }}
          </div>
          <div v-if="toast.message" class="text-sm text-muted-foreground mt-1">
            {{ toast.message }}
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <!-- Action Button -->
          <button
            v-if="toast.action"
            :class="actionButtonClasses"
            @click="handleAction"
          >
            {{ toast.action.label }}
          </button>

          <!-- Dismiss Button -->
          <button
            v-if="toast.dismissible"
            :class="dismissButtonClasses"
            @click="handleDismiss"
            aria-label="Dismiss notification"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import { rfpCn } from '@/utils/rfpUtils.js'
import { rfpUseToast } from '@/composables/rfpUseToast.js'

// Props interface
interface Props {
  toast?: RfpToast
}

// Props
const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  dismiss: [id: string]
  action: [id: string]
}>()

// Icon mapping
const iconMap = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info
}

// Computed icon component
const iconComponent = computed(() => {
  return iconMap[props.toast?.type || 'info']
})

// Base toast classes
const baseClasses = 'pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border bg-background shadow-lg'

// Type-specific classes
const typeClasses = {
  success: 'border-green-200 bg-green-50 text-green-900',
  error: 'border-red-200 bg-red-50 text-red-900',
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-900',
  info: 'border-blue-200 bg-blue-50 text-blue-900'
}

// Computed toast classes
const toastClasses = computed(() => {
  if (!props.toast) return ''
  
  return rfpCn(
    baseClasses,
    typeClasses[props.toast.type],
    'p-4'
  )
})

// Computed icon classes
const iconClasses = computed(() => {
  if (!props.toast) return ''
  
  const iconTypeClasses = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-yellow-600',
    info: 'text-blue-600'
  }
  
  return rfpCn(
    'flex-shrink-0 mt-0.5',
    iconTypeClasses[props.toast.type]
  )
})

// Computed action button classes
const actionButtonClasses = computed(() => {
  if (!props.toast) return ''
  
  const actionTypeClasses = {
    success: 'bg-green-600 text-white hover:bg-green-700',
    error: 'bg-red-600 text-white hover:bg-red-700',
    warning: 'bg-yellow-600 text-white hover:bg-yellow-700',
    info: 'bg-blue-600 text-white hover:bg-blue-700'
  }
  
  return rfpCn(
    'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
    actionTypeClasses[props.toast.type]
  )
})

// Computed dismiss button classes
const dismissButtonClasses = computed(() => {
  if (!props.toast) return ''
  
  const dismissTypeClasses = {
    success: 'text-green-600 hover:text-green-800',
    error: 'text-red-600 hover:text-red-800',
    warning: 'text-yellow-600 hover:text-yellow-800',
    info: 'text-blue-600 hover:text-blue-800'
  }
  
  return rfpCn(
    'flex-shrink-0 p-1 rounded-md transition-colors',
    dismissTypeClasses[props.toast.type]
  )
})

// Event handlers
const handleDismiss = () => {
  if (props.toast) {
    emit('dismiss', props.toast.id)
  }
}

const handleAction = () => {
  if (props.toast?.action) {
    props.toast.action.handler()
    emit('action', props.toast.id)
  }
}
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
