<template>
  <div
    :class="separatorClasses"
    :role="role"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  orientation?: 'horizontal' | 'vertical'
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  orientation: 'horizontal'
})

const separatorClasses = computed(() => {
  return rfpCn(
    'shrink-0 bg-border',
    props.orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
    props.className
  )
})

const role = computed(() => props.orientation === 'horizontal' ? 'separator' : undefined)
</script>

