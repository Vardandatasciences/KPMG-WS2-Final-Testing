<template>
  <div @click="$emit('open')" class="inline-block">
    <slot />
  </div>
</template>

<script setup>
defineEmits(['open'])
</script>
