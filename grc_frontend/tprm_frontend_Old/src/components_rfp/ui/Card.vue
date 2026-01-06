<template>
  <div :class="cardClasses">
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

const cardClasses = computed(() => {
  return rfpCn(
    'rounded-lg border bg-card text-card-foreground shadow-sm',
    props.className
  )
})
</script>

