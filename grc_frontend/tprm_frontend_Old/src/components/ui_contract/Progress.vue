<template>
  <div
    :class="[
      'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <div
      :class="[
        'h-full w-full flex-1 bg-primary transition-all',
        $attrs.class
      ]"
      :style="{ width: `${modelValue}%` }"
    />
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Number,
    default: 0
  }
})
</script>
