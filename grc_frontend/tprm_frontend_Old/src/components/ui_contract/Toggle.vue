<template>
  <button
    :class="[
      'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors hover:bg-muted hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground',
      pressed ? 'data-[state=on]' : '',
      $attrs.class
    ]"
    v-bind="$attrs"
    @click="$emit('update:pressed', !pressed)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  pressed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:pressed'])
</script>
