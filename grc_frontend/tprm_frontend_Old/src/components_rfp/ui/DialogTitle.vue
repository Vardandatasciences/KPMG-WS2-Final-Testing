<template>
  <h2 :class="titleClasses">
    <slot />
  </h2>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  className?: string
}

const props = defineProps<Props>()

const titleClasses = computed(() => {
  return rfpCn(
    'text-lg font-semibold leading-none tracking-tight',
    props.className
  )
})
</script>
