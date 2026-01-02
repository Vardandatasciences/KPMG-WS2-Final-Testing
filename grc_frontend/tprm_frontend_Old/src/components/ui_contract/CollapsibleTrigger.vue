<template>
  <button
    :class="[
      'flex w-full items-center justify-between py-4 font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
    <svg
      class="h-4 w-4 shrink-0 transition-transform duration-200"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <polyline points="6,9 12,15 18,9" />
    </svg>
  </button>
</template>

<script setup>
// Collapsible trigger component
</script>
