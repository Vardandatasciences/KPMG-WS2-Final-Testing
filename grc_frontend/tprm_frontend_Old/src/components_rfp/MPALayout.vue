<template>
  <div class="min-h-screen bg-background">
    <!-- Navigation -->
    <MPANavigation />
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import MPANavigation from './MPANavigation.vue'
</script>

