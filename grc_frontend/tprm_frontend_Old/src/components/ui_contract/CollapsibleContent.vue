<template>
  <div
    :class="[
      'overflow-hidden text-sm transition-all data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <div class="pb-4 pt-0">
      <slot />
    </div>
  </div>
</template>

<script setup>
// Collapsible content component
</script>
