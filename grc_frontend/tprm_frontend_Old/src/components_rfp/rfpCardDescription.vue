<template>
  <p :class="descriptionClasses">
    <slot />
  </p>
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

// Computed description classes
const descriptionClasses = computed(() => {
  return rfpCn(
    'text-sm text-muted-foreground',
    props.className
  )
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
