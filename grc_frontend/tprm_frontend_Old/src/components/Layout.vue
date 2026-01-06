<template>
  <div style="min-height: 100vh; display: flex; width: 100%; background: #f8f9fa;">
    <AppSidebar />
    
    <div style="flex: 1; display: flex; flex-direction: column; margin-left: 256px;">
      <Header />
      
      <main style="flex: 1; padding: 1.5rem; background: white;">
        <slot />
      </main>
    </div>
  </div>
  
</template>

<script setup>
import AppSidebar from '@/components/contract/AppSidebar.vue'
import Header from '@/components/contract/Header.vue'
</script>