<template>
  <textarea
    :id="id"
    :class="cn(
      'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
      className
    )"
    :placeholder="placeholder"
    :disabled="disabled"
    :rows="rows"
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  id: String,
  className: String,
  placeholder: String,
  disabled: Boolean,
  rows: {
    type: Number,
    default: 3
  },
  modelValue: String
})

const emit = defineEmits(['update:modelValue'])
</script>
