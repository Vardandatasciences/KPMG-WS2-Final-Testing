<template>
  <div :class="badgeClasses">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

// Props interface
interface Props {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline'
  className?: string
}

// Default props
const props = withDefaults(defineProps<Props>(), {
  variant: 'default'
})

// Base badge classes
const baseClasses = 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'

// Variant classes
const variantClasses = {
  default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
  secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
  destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
  outline: 'text-foreground'
}

// Computed badge classes
const badgeClasses = computed(() => {
  return rfpCn(
    baseClasses,
    variantClasses[props.variant],
    props.className
  )
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
