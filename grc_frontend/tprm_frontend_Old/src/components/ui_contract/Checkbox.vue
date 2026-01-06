<template>
  <div class="flex items-center space-x-2">
    <input
      type="checkbox"
      :class="[
        'h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary focus:ring-offset-2',
        $attrs.class
      ]"
      v-bind="$attrs"
    />
    <label
      v-if="$slots.default"
      :for="$attrs.id"
      class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
    >
      <slot />
    </label>
  </div>
</template>

<script setup>
// Checkbox component with label support
</script>
