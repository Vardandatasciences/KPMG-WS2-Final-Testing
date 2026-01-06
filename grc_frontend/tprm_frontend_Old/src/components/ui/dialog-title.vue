<template>
  <h2 :class="cn('text-lg font-semibold leading-none tracking-tight', className)">
    <slot />
  </h2>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  className: String
})
</script>