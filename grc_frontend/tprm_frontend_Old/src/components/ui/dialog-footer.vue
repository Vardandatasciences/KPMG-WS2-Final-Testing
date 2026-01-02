<template>
  <div :class="cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-4', className)">
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  className: String
})
</script>