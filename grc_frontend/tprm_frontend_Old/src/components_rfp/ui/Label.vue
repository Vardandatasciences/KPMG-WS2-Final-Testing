<template>
  <label
    :class="labelClasses"
    :for="htmlFor"
  >
    <slot />
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  htmlFor?: string
  className?: string
}

const props = defineProps<Props>()

const labelClasses = computed(() => {
  return rfpCn(
    'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
    props.className
  )
})
</script>

