<template>
  <div
    :class="[
      'inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
  </div>
</template>

<script setup>
// Tabs list component
</script>
