<template>
  <span :class="cn('block truncate', className)">
    {{ placeholder }}
  </span>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  placeholder: String,
  className: String
})
</script>