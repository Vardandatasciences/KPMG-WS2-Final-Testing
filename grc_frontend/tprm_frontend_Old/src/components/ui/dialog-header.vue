<template>
  <div :class="cn('flex flex-col space-y-1.5 text-center sm:text-left mb-4', className)">
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  className: String
})
</script>