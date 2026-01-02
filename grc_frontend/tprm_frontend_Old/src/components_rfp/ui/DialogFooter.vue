<template>
  <div :class="footerClasses">
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

const footerClasses = computed(() => {
  return rfpCn(
    'flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-6',
    props.className
  )
})
</script>
