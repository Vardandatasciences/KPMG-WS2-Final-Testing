<template>
  <p :class="descriptionClasses">
    <slot />
  </p>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  className?: string
}

const props = defineProps<Props>()

const descriptionClasses = computed(() => {
  return rfpCn(
    'text-sm text-muted-foreground',
    props.className
  )
})
</script>
