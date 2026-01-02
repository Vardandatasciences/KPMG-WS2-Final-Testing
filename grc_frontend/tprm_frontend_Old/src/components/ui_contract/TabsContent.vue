<template>
  <div
    v-show="isActive"
    :class="[
      'mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      $attrs.class
    ]"
    v-bind="$attrs"
  >
    <slot />
  </div>
</template>

<script setup>
import { inject, computed, ref } from 'vue'

const props = defineProps({
  value: {
    type: String,
    required: true
  }
})

const activeTab = inject('activeTab', ref(''))

const isActive = computed(() => activeTab.value === props.value)
</script>
