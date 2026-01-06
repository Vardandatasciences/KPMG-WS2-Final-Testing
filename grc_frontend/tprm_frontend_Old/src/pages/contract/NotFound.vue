<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center">
      <h1 class="text-4xl font-bold mb-4">Page Not Found</h1>
      <p class="text-xl text-muted-foreground mb-8">The page you're looking for doesn't exist.</p>
      <div class="space-x-4">
        <button @click="go('/')" class="inline-flex h-9 items-center rounded-md bg-primary px-4 text-primary-foreground hover:bg-primary/90">
          Go to Dashboard
        </button>
        <button @click="goBack" class="inline-flex h-9 items-center rounded-md border px-4 text-sm hover:bg-muted/50">
          Go Back
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const go = (path: string) => router.push(path)
const goBack = () => router.go(-1)
</script>
