<template>
  <div :class="cn('p-6', className)">
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  className: String
})
</script>