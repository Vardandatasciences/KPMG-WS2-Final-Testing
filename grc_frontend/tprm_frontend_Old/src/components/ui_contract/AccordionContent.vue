<template>
  <div
    :class="[
      'overflow-hidden text-sm transition-all',
      isOpen ? 'animate-accordion-down' : 'animate-accordion-up',
      $attrs.class
    ]"
    :data-state="isOpen ? 'open' : 'closed'"
  >
    <div class="pb-4 pt-0">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { inject, computed } from 'vue'

const props = defineProps({
  value: {
    type: String,
    required: true
  }
})

const accordion = inject('accordion')
const isOpen = computed(() => accordion.isOpen(props.value))
</script>
