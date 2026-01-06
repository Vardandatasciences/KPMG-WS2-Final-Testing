<template>
  <div :class="footerClasses">
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

// Computed footer classes
const footerClasses = computed(() => {
  return rfpCn(
    'flex items-center p-6 pt-0',
    props.className
  )
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
