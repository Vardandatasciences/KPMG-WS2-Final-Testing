<template>
  <td
    :class="[
      'p-4 align-middle [&:has([role=checkbox])]:pr-0',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
  </td>
</template>

<script setup>
// Table cell component
</script>
