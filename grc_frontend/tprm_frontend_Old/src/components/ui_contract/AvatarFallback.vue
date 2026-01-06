<template>
  <div
    :class="[
      'flex h-full w-full items-center justify-center rounded-full bg-muted',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
  </div>
</template>

<script setup>
// Avatar fallback component
</script>
