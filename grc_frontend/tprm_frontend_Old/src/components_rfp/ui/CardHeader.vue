<template>
  <div :class="headerClasses">
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

const headerClasses = computed(() => {
  return rfpCn(
    'flex flex-col space-y-1.5 p-6',
    props.className
  )
})
</script>

