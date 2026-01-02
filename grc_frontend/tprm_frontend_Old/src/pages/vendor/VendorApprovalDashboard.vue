<!-- SamplePage.vue -->
<template>
    <section class="page">
      <header class="page__header">
        <h1>TPEM Dashboard — Sample</h1>
        <p class="page__subtitle">Minimal Vue 3 page with fetch, search, form, and state.</p>
      </header>
  
      <!-- KPI Cards -->
      <div class="kpis">
        <div class="card">
          <div class="card__title">Total Items</div>
          <div class="card__value">{{ items.length }}</div>
        </div>
        <div class="card">
          <div class="card__title">Filtered</div>
          <div class="card__value">{{ filteredItems.length }}</div>
        </div>
        <div class="card">
          <div class="card__title">Form Submits</div>
          <div class="card__value">{{ submitCount }}</div>
        </div>
      </div>
  
      <!-- Controls -->
      <div class="controls">
        <input
          v-model.trim="query"
          type="search"
          placeholder="Search title…"
          class="input"
          @input="handleSearch"
        />
        <button class="btn" :disabled="loading" @click="loadData">
          {{ loading ? 'Loading…' : 'Reload Data' }}
        </button>
      </div>
  
      <!-- Status / Errors -->
      <p v-if="error" class="error">⚠️ {{ error }}</p>
  
      <!-- List -->
      <div class="list" v-if="!loading && filteredItems.length">
        <article class="list__item" v-for="item in filteredItems" :key="item.id">
          <h3>{{ item.title }}</h3>
          <p>{{ item.body }}</p>
        </article>
      </div>
      <p v-else-if="!loading && !filteredItems.length" class="muted">No results.</p>
  
      <hr class="divider" />
  
      <!-- Simple Form -->
      <form class="form" @submit.prevent="handleSubmit">
        <h2>Create Note</h2>
        <label class="form__row">
          <span>Title</span>
          <input v-model.trim="form.title" class="input" placeholder="Enter title" required />
        </label>
        <label class="form__row">
          <span>Description</span>
          <textarea v-model.trim="form.desc" class="input" rows="3" placeholder="Enter description"></textarea>
        </label>
  
        <div class="form__actions">
          <button class="btn" type="submit">Save</button>
          <button class="btn btn--ghost" type="button" @click="resetForm">Reset</button>
        </div>
  
        <p v-if="lastSaved" class="success">✅ Saved “{{ lastSaved.title }}”.</p>
      </form>
    </section>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import loggingService from '@/services/loggingService'
  
  // state
  const items = ref([])
  const loading = ref(false)
  const error = ref('')
  const query = ref('')
  
  // derived
  const filteredItems = computed(() => {
    if (!query.value) return items.value
    const q = query.value.toLowerCase()
    return items.value.filter(
      (i) => i.title.toLowerCase().includes(q) || i.body.toLowerCase().includes(q)
    )
  })
  
  // demo form state
  const form = ref({ title: '', desc: '' })
  const lastSaved = ref(null)
  const submitCount = ref(0)
  
  // methods
  async function loadData() {
    loading.value = true
    error.value = ''
    try {
      // Demo API: replace with your backend `/api/...`
      const res = await fetch('https://jsonplaceholder.typicode.com/posts?_limit=8')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      items.value = await res.json()
    } catch (e) {
      error.value = `Failed to load data: ${e.message}`
    } finally {
      loading.value = false
    }
  }
  
  function handleSearch() {
    // No-op; computed takes care of filtering. Kept for extensibility/logging.
  }
  
  function handleSubmit() {
    // In real apps, POST to your API here.
    lastSaved.value = { ...form.value, id: Date.now() }
    submitCount.value++
    resetForm()
  }
  
  function resetForm() {
    form.value = { title: '', desc: '' }
  }
  
  onMounted(async () => {
    await loggingService.logPageView('Vendor', 'Vendor Approval Dashboard')
    await loadData()
  })
  </script>
  
  <style scoped>
  .page {
    max-width: 980px;
    margin: 24px auto;
    padding: 16px;
  }
  
  .page__header {
    margin-bottom: 16px;
  }
  .page__subtitle {
    color: #667085;
    margin-top: 4px;
  }
  
  .kpis {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 16px 0 8px;
  }
  .card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 12px 14px;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
  }
  .card__title {
    font-size: 12px;
    color: #667085;
    margin-bottom: 4px;
  }
  .card__value {
    font-size: 24px;
    font-weight: 700;
  }
  
  .controls {
    display: flex;
    gap: 8px;
    margin: 12px 0 6px;
  }
  
  .input {
    flex: 1 1 auto;
    padding: 10px 12px;
    border: 1px solid #d0d5dd;
    border-radius: 10px;
    font-size: 14px;
    outline: none;
  }
  .input:focus {
    border-color: #7c3aed; /* you can move this to global CSS */
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
  }
  
  .btn {
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid #7c3aed;
    background: #7c3aed;
    color: #fff;
    font-weight: 600;
    cursor: pointer;
  }
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .btn--ghost {
    background: transparent;
    color: #7c3aed;
  }
  
  .error { color: #b42318; margin: 8px 0; }
  .success { color: #027a48; margin-top: 8px; }
  .muted { color: #98a2b3; }
  
  .list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 12px 0;
  }
  .list__item {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 12px;
  }
  .list__item h3 {
    margin: 0 0 6px;
    font-size: 16px;
  }
  
  .divider {
    margin: 20px 0;
    border: 0;
    border-top: 1px solid #eee;
  }
  
  .form {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
  }
  .form__row {
    display: grid;
    grid-template-columns: 120px 1fr;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }
  .form__actions {
    display: flex;
    gap: 8px;
    margin-top: 8px;
  }
  
  /* Responsive */
  @media (max-width: 720px) {
    .kpis { grid-template-columns: 1fr; }
    .list { grid-template-columns: 1fr; }
    .form__row { grid-template-columns: 1fr; }
  }
  </style>
  