<template>
  <div class="relative inline-block">
    <div
      @mouseenter="show = true"
      @mouseleave="show = false"
      class="inline-block"
    >
      <slot />
    </div>
    <div
      v-if="show"
      :class="[
        'absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-md shadow-lg',
        position === 'top' ? 'bottom-full left-1/2 transform -translate-x-1/2 mb-2' : '',
        position === 'bottom' ? 'top-full left-1/2 transform -translate-x-1/2 mt-2' : '',
        position === 'left' ? 'right-full top-1/2 transform -translate-y-1/2 mr-2' : '',
        position === 'right' ? 'left-full top-1/2 transform -translate-y-1/2 ml-2' : '',
        $attrs.class
      ]"
    >
      {{ content }}
      <div
        :class="[
          'absolute w-2 h-2 bg-gray-900 transform rotate-45',
          position === 'top' ? 'top-full left-1/2 transform -translate-x-1/2' : '',
          position === 'bottom' ? 'bottom-full left-1/2 transform -translate-x-1/2' : '',
          position === 'left' ? 'left-full top-1/2 transform -translate-y-1/2' : '',
          position === 'right' ? 'right-full top-1/2 transform -translate-y-1/2' : ''
        ]"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  content: {
    type: String,
    required: true
  },
  position: {
    type: String,
    default: 'top'
  }
})

const show = ref(false)
</script>
