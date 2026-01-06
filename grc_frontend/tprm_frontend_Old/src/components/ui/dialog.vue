<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="fixed inset-0 bg-black/50" @click="$emit('update:open', false)"></div>
    <div class="relative bg-background rounded-lg shadow-lg max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
      <slot />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  open: Boolean
})

const emit = defineEmits(['update:open'])
</script>