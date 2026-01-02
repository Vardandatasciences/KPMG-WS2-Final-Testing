<template>
  <MPALayout>
    <component :is="component" v-bind="componentProps" />
  </MPALayout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MPALayout from './MPALayout.vue'

const props = defineProps<{
  component: any
  componentProps?: Record<string, any>
}>()

const component = computed(() => props.component)
const componentProps = computed(() => props.componentProps || {})
</script>
