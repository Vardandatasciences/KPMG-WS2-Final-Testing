<template>
  <div class="flex items-center space-x-2">
    <input
      :id="id"
      :class="checkboxClasses"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      :required="required"
      @change="handleChange"
    />
    <label
      v-if="$slots.default"
      :for="id"
      class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
    >
      <slot />
    </label>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn, rfpGenerateId } from '@/utils/rfpUtils.js'

interface Props {
  modelValue?: boolean
  disabled?: boolean
  required?: boolean
  id?: string
  className?: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  required: false
})

// Generate ID if not provided
const id = props.id || rfpGenerateId()

const emit = defineEmits<Emits>()

const checkboxClasses = computed(() => {
  return rfpCn(
    'peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground',
    props.className
  )
})

const handleChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.checked)
}
</script>

