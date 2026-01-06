<template>
  <tbody :class="['[&_tr:last-child]:border-0', $attrs.class]">
    <slot />
  </tbody>
</template>

<script setup>
// Table body component
</script>
