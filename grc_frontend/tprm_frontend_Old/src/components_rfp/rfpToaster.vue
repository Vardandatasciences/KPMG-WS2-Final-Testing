<template>
  <Teleport to="body">
    <div
      class="fixed top-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]"
      aria-live="polite"
      aria-label="Notifications"
    >
      <RfpToast
        v-for="toast in toasts"
        :key="toast.id"
        :toast="toast"
        @dismiss="handleDismiss"
        @action="handleAction"
      />
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import RfpToast from './rfpToast.vue'

// Use toast composable
const { toasts, removeToast } = rfpUseToast()

// Event handlers
const handleDismiss = (id: string) => {
  removeToast(id)
}

const handleAction = (id: string) => {
  // Action is handled by the toast component itself
  // This is just for consistency with the event system
}
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
