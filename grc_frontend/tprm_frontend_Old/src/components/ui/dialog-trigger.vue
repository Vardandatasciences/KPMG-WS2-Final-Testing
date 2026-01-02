<template>
  <div @click="$emit('click')">
    <slot />
  </div>
</template>

<script setup>
const emit = defineEmits(['click'])
</script>