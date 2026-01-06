<template>
  <div class="access-denied-container">
    <!-- Red circular icon with white X -->
    <div class="error-icon">
      <div class="x-symbol">✕</div>
    </div>
    
    <!-- Title -->
    <h1 class="access-denied-title">Access Denied</h1>
    
    <!-- Description -->
    <p class="error-message">You do not have permission to view this page.</p>
    <p class="error-message">Please check your credentials and try again.</p>
    
    <!-- Error Code -->
    <p class="error-code">Error Code: 403</p>
  </div>
</template>

<script setup>
// Simple component - no complex logic needed
</script>

<style scoped>
.access-denied-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  padding: 20px;
}

.error-icon {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #dc3545;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
}

.x-symbol {
  color: white;
  font-size: 60px;
  font-weight: bold;
  line-height: 1;
}

.access-denied-title {
  font-size: 36px;
  font-weight: bold;
  color: #333;
  margin: 0 0 20px 0;
  text-align: center;
}

.error-message {
  font-size: 16px;
  color: #333;
  margin: 8px 0;
  text-align: center;
}

.error-code {
  font-size: 14px;
  color: #333;
  margin-top: 30px;
  text-align: center;
}
</style>
