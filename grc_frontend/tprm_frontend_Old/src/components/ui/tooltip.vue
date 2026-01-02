<template>
  <div class="relative inline-block">
    <slot />
  </div>
</template>

<script setup>
import { provide } from 'vue'

provide('tooltip', {})
</script>
