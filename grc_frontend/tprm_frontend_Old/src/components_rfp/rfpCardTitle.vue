<template>
  <h3 :class="titleClasses">
    <slot />
  </h3>
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

// Computed title classes
const titleClasses = computed(() => {
  return rfpCn(
    'text-2xl font-semibold leading-none tracking-tight',
    props.className
  )
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
