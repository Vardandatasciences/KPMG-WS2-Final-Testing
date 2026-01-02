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
    'p-6 pt-0',
    props.className
  )
})
</script>

