<template>
  <div
    :class="cn(
      'relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      className
    )"
    @click="$emit('select', value)"
  >
    <slot />
  </div>
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  value: String,
  className: String
})

const emit = defineEmits(['select'])
</script>