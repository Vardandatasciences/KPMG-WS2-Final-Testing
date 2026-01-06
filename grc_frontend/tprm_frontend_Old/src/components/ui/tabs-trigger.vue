<template>
  <button
    :class="cn(
      'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
      active ? 'bg-background text-foreground shadow-sm' : 'hover:bg-background/50',
      className
    )"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  value: String,
  active: Boolean,
  className: String
})

const emit = defineEmits(['click'])
</script>