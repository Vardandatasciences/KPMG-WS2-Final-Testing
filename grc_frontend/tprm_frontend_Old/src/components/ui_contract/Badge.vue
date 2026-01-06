<template>
  <div 
    class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
    :class="[
      variant === 'outline' ? 'border-input bg-background hover:bg-accent hover:text-accent-foreground' : 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
      $attrs.class
    ]"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default'
  }
})
</script>
