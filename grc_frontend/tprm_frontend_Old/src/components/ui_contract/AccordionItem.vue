<template>
  <div :class="['border-b', $attrs.class]" :data-state="isOpen ? 'open' : 'closed'">
    <slot />
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
