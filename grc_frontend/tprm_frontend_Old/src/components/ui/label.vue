<template>
  <label
    :for="htmlFor"
    :class="cn(
      'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
      className
    )"
  >
    <slot />
  </label>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  htmlFor: String,
  className: String
})
</script>
