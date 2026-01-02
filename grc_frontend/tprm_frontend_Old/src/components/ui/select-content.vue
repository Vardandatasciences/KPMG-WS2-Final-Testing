<template>
  <div
    v-if="isOpen"
    :class="cn(
      'relative z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md',
      className
    )"
  >
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  className: String
})
</script>