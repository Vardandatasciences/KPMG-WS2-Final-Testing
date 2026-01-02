<template>
  <div class="relative">
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

defineEmits(['update:modelValue'])
</script>
