<template>
  <div
    :class="[
      'z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none',
      $attrs.class
    ]"
  >
    <slot />
  </div>
</template>

<script setup>
// Popover content component
</script>
