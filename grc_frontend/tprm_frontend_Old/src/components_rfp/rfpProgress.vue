<template>
  <div :class="progressClasses">
    <div 
      :class="indicatorClasses"
      :style="indicatorStyle"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

// Props interface
interface Props {
  value?: number
  max?: number
  className?: string
}

// Default props
const props = withDefaults(defineProps<Props>(), {
  value: 0,
  max: 100,
  className: ''
})

// Computed progress classes
const progressClasses = computed(() => {
  return rfpCn(
    'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
    props.className
  )
})

// Computed indicator classes
const indicatorClasses = computed(() => {
  return 'h-full w-full flex-1 bg-primary transition-all'
})

// Computed indicator style
const indicatorStyle = computed(() => {
  const percentage = Math.min(Math.max((props.value / props.max) * 100, 0), 100)
  return {
    transform: `translateX(-${100 - percentage}%)`
  }
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
