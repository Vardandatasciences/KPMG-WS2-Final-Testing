<template>
  <option :value="value" :disabled="disabled">
    <slot />
  </option>
</template>

<script setup lang="ts">
interface Props {
  value: string
  disabled?: boolean
}

defineProps<Props>()
</script>

