<template>
  <h3 :class="titleClasses">
    <slot />
  </h3>
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
    'text-2xl font-semibold leading-none tracking-tight',
    props.className
  )
})
</script>

