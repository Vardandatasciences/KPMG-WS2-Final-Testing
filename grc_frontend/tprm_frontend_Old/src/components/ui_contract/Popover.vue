<template>
  <div class="relative inline-block">
    <div @click="open = !open" class="inline-block">
      <slot name="trigger" />
    </div>
    <div
      v-if="open"
      :class="[
        'absolute z-50 mt-2 w-64 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none',
        $attrs.class
      ]"
      @click.self="open = false"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const open = ref(false)
</script>
