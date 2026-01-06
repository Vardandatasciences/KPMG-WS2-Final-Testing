<template>
  <div class="relative">
    <slot />
  </div>
</template>

<script setup>
import { provide, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const selectedValue = ref(props.modelValue)

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  selectedValue.value = newValue
})

const open = () => {
  isOpen.value = true
}

const close = () => {
  isOpen.value = false
}

const select = (value) => {
  selectedValue.value = value
  emit('update:modelValue', value)
  close()
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    close()
  }
}

// Add click outside listener
if (typeof window !== 'undefined') {
  document.addEventListener('click', handleClickOutside)
}

provide('select', {
  isOpen,
  selectedValue,
  open,
  close,
  select
})
</script>
