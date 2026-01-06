<template>
  <div class="flex items-center space-x-2">
    <input
      type="radio"
      :id="$attrs.id"
      :value="$attrs.value"
      :checked="modelValue === $attrs.value"
      @change="$emit('update:modelValue', $attrs.value)"
      class="h-4 w-4 border-gray-300 text-primary focus:ring-primary focus:ring-offset-2"
    />
    <label
      :for="$attrs.id"
      class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
    >
      <slot />
    </label>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  }
})

defineEmits(['update:modelValue'])
</script>
