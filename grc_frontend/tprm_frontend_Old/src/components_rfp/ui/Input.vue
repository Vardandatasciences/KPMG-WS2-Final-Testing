<template>
  <input
    :class="inputClasses"
    :type="type"
    :placeholder="placeholder"
    :value="modelValue"
    :disabled="disabled"
    :required="required"
    @input="handleInput"
    @blur="handleBlur"
    @focus="handleFocus"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'tel' | 'url'
  placeholder?: string
  modelValue?: string | number
  disabled?: boolean
  required?: boolean
  className?: string
}

interface Emits {
  (e: 'update:modelValue', value: string | number): void
  (e: 'blur', event: FocusEvent): void
  (e: 'focus', event: FocusEvent): void
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  disabled: false,
  required: false
})

const emit = defineEmits<Emits>()

const inputClasses = computed(() => {
  return rfpCn(
    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    props.className
  )
})

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = props.type === 'number' ? Number(target.value) : target.value
  emit('update:modelValue', value)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}
</script>

