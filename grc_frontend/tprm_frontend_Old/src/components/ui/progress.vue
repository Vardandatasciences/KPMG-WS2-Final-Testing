<template>
  <div
    :class="cn(
      'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
      className
    )"
  >
    <div
      class="h-full w-full flex-1 bg-primary transition-all"
      :style="{ transform: `translateX(-${100 - (value || 0)}%)` }"
    />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  className: String
})
</script>
