<template>
  <tr
    :class="[
      'border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
  </tr>
</template>

<script setup>
// Table row component
</script>
