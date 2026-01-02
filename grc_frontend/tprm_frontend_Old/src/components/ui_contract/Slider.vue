<template>
  <div
    :class="[
      'relative flex w-full touch-none select-none items-center',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <input
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :value="modelValue"
      @input="$emit('update:modelValue', Number($event.target.value))"
      class="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary"
    />
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Number,
    default: 0
  },
  min: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
  },
  step: {
    type: Number,
    default: 1
  }
})

defineEmits(['update:modelValue'])
</script>
