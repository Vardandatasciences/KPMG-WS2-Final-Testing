<template>
  <div :class="contentClasses">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  className?: string
}

const props = defineProps<Props>()

const contentClasses = computed(() => {
  return rfpCn(
    'relative bg-white rounded-lg shadow-lg border border-gray-200 p-6 w-full max-h-[90vh] overflow-y-auto',
    props.className
  )
})
</script>
