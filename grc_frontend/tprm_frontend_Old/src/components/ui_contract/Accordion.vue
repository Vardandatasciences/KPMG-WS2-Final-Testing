<template>
  <div class="w-full">
    <slot />
  </div>
</template>

<script setup>
import { provide, ref } from 'vue'

const openItems = ref(new Set())

const toggleItem = (value) => {
  if (openItems.value.has(value)) {
    openItems.value.delete(value)
  } else {
    openItems.value.add(value)
  }
}

const isOpen = (value) => openItems.value.has(value)

provide('accordion', {
  openItems,
  toggleItem,
  isOpen
})
</script>
