<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center"
    @click.self="$emit('close')"
  >
    <div class="fixed inset-0 bg-black/50" />
    <div
      :class="[
        'relative z-50 w-full max-w-lg rounded-lg bg-background p-6 shadow-lg',
        $attrs.class
      ]"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])
</script>
