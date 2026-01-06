<template>
  <div :class="headerClasses">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

// Props interface
interface Props {
  className?: string
}

// Props
const props = defineProps<Props>()

// Computed header classes
const headerClasses = computed(() => {
  return rfpCn(
    'flex flex-col space-y-1.5 p-6',
    props.className
  )
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
