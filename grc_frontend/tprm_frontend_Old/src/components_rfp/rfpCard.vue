<template>
  <div :class="cardClasses">
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

// Computed card classes
const cardClasses = computed(() => {
  return rfpCn(
    'rounded-lg border bg-card text-card-foreground shadow-sm',
    props.className
  )
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
