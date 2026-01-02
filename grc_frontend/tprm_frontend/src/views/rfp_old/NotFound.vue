<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-primary mb-4">404</h1>
      <h2 class="text-2xl font-semibold text-foreground mb-4">Page Not Found</h2>
      <p class="text-muted-foreground mb-8">The page you're looking for doesn't exist.</p>
      <RfpButton @click="goHome">
        Go Home
      </RfpButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import RfpButton from '@/components_rfp/rfpButton.vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>
