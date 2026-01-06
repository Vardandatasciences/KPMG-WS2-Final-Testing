<template>
  <span :class="valueClasses">
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  placeholder?: string
  className?: string
}

const props = defineProps<Props>()

const valueClasses = computed(() => {
  return rfpCn(
    'block truncate',
    props.className
  )
})
</script>
