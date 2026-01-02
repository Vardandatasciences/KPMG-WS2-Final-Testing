<template>
  <button
    :class="[
      'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm',
      $attrs.class
    ]"
    :data-state="isActive ? 'active' : 'inactive'"
    @click="handleClick"
    v-bind="$attrs"
  >
    <slot />
  </button>
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

const handleClick = () => {
  activeTab.value = props.value
}
</script>
