<template>
  <div :class="['p-3', $attrs.class]">
    <div class="flex items-center justify-center pt-1">
      <div class="text-sm font-medium">Calendar</div>
    </div>
    <div class="mt-3 grid grid-cols-7 text-center text-xs leading-6 text-muted-foreground">
      <div>Su</div>
      <div>Mo</div>
      <div>Tu</div>
      <div>We</div>
      <div>Th</div>
      <div>Fr</div>
      <div>Sa</div>
    </div>
    <div class="mt-2 grid grid-cols-7 gap-1 text-center text-sm">
      <slot />
    </div>
  </div>
</template>

<script setup>
// Calendar component
</script>
