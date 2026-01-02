<template>
  <component
    :is="tag"
    :class="buttonClasses"
    :disabled="disabled"
    :type="tag === 'button' ? type : undefined"
    @click="handleClick"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

// Props interface
interface Props {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  disabled?: boolean
  asChild?: boolean
  type?: 'button' | 'submit' | 'reset'
}

// Default props
const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'default',
  disabled: false,
  asChild: false,
  type: 'button'
})

// Emits
const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// Computed tag based on asChild prop
const tag = computed(() => props.asChild ? 'div' : 'button')

// Base button classes
const baseClasses = 'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0'

// Variant classes
const variantClasses = {
  default: 'bg-primary text-primary-foreground hover:bg-primary/90',
  destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  link: 'text-primary underline-offset-4 hover:underline'
}

// Size classes
const sizeClasses = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-md px-3',
  lg: 'h-11 rounded-md px-8',
  icon: 'h-10 w-10'
}

// Computed button classes
const buttonClasses = computed(() => {
  return rfpCn(
    baseClasses,
    variantClasses[props.variant],
    sizeClasses[props.size]
  )
})

// Click handler
const handleClick = (event: MouseEvent) => {
  if (!props.disabled) {
    emit('click', event)
  }
}
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
