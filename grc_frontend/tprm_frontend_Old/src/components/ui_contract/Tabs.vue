<template>
  <div class="w-full">
    <slot />
  </div>
</template>

<script setup>
import { provide, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const activeTab = ref(props.modelValue)

// Provide active tab to child components
provide('activeTab', activeTab)

// Watch for prop changes
watch(() => props.modelValue, (newValue) => {
  activeTab.value = newValue
})

// Watch for local changes
watch(activeTab, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>
