<template>
  <div :class="cn('space-y-4', className)">
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  defaultValue: String,
  className: String
})
</script>