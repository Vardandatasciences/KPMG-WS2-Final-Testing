<template>
  <a
    :class="[
      'transition-colors hover:text-foreground',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
  </a>
</template>

<script setup>
// Breadcrumb link component
</script>
