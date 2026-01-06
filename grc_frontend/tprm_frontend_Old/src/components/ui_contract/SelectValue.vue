<template>
  <span :class="['block truncate', $attrs.class]">
    <slot v-if="selectedValue">{{ selectedValue }}</slot>
    <span v-else class="text-muted-foreground">{{ placeholder }}</span>
  </span>
</template>

<script setup>
import { inject } from 'vue'

const { selectedValue } = inject('select', { selectedValue: '' })

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Select an option'
  }
})
</script>
