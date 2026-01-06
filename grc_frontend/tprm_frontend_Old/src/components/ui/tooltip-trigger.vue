<template>
  <div @mouseenter="showTooltip" @mouseleave="hideTooltip">
    <slot />
  </div>
</template>

<script setup>
import { inject } from 'vue'

const showTooltip = () => {
  // Tooltip logic
}
const hideTooltip = () => {
  // Tooltip logic
}
</script>
