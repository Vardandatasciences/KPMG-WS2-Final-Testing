<template>
  <div class="tenant-switcher" v-if="isMultiTenant" ref="container">
    <button class="switcher-btn" @click="open = !open" :class="{ active: open }">
      <span class="tenant-avatar">{{ initials(currentTenant?.name) }}</span>
      <span class="tenant-name">{{ currentTenant?.name || 'Select Tenant' }}</span>
      <i class="fas fa-chevron-down chevron" :class="{ rotated: open }"></i>
    </button>

    <transition name="dropdown">
      <div v-if="open" class="switcher-dropdown">
        <div class="dropdown-header">Switch Tenant</div>
        <div
          v-for="tenant in allowedTenants"
          :key="tenant.id"
          class="tenant-item"
          :class="{ current: tenant.id === currentTenant?.id }"
          @click="switchTenant(tenant)"
        >
          <span class="item-avatar">{{ initials(tenant.name) }}</span>
          <div class="item-info">
            <div class="item-name">{{ tenant.name }}</div>
            <div class="item-sub">{{ tenant.subdomain }}</div>
          </div>
          <i v-if="tenant.id === currentTenant?.id" class="fas fa-check check-icon"></i>
          <i v-if="switching === tenant.id" class="fas fa-spinner fa-spin loading-icon"></i>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { useTenantStore } from '@/stores/tenant.js'

export default {
  name: 'TenantSwitcher',
  data() {
    return {
      open: false,
      switching: null,
      tenantStore: null,
    }
  },
  computed: {
    currentTenant() { return this.tenantStore?.currentTenant },
    allowedTenants() { return this.tenantStore?.allowedTenants ?? [] },
    isMultiTenant() { return this.allowedTenants.length > 1 },
  },
  mounted() {
    this.tenantStore = useTenantStore()
    document.addEventListener('click', this.handleOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  methods: {
    async switchTenant(tenant) {
      if (tenant.id === this.currentTenant?.id) { this.open = false; return }
      this.switching = tenant.id
      try {
        await this.tenantStore.switchTenant(tenant.id)
        this.open = false
        window.location.reload()
      } catch (e) {
        console.error('[TenantSwitcher] switch failed:', e.message)
      } finally {
        this.switching = null
      }
    },
    initials(name) {
      if (!name) return '?'
      return name.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase()
    },
    handleOutsideClick(e) {
      if (this.$refs.container && !this.$refs.container.contains(e.target)) {
        this.open = false
      }
    },
  },
}
</script>

<style scoped>
.tenant-switcher { position: relative; }
.switcher-btn { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px 12px; cursor: pointer; color: inherit; font-size: 14px; font-weight: 500; transition: background 0.15s; }
.switcher-btn:hover, .switcher-btn.active { background: rgba(255,255,255,0.2); }
.tenant-avatar { width: 26px; height: 26px; border-radius: 6px; background: rgba(255,255,255,0.25); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.tenant-name { max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chevron { font-size: 10px; transition: transform 0.2s; }
.chevron.rotated { transform: rotate(180deg); }
.switcher-dropdown { position: absolute; top: calc(100% + 8px); left: 0; min-width: 220px; background: #fff; border-radius: 10px; box-shadow: 0 4px 24px rgba(0,0,0,0.15); z-index: 2000; overflow: hidden; }
.dropdown-header { padding: 10px 14px; font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.7px; border-bottom: 1px solid #f0f0f0; }
.tenant-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; transition: background 0.15s; }
.tenant-item:hover { background: #f5f7ff; }
.tenant-item.current { background: #f0f4ff; }
.item-avatar { width: 30px; height: 30px; border-radius: 7px; background: #e8eaf6; color: #3f51b5; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.item-name { font-size: 14px; font-weight: 600; color: #333; }
.item-sub { font-size: 12px; color: #888; }
.check-icon { margin-left: auto; color: #3f51b5; font-size: 12px; }
.loading-icon { margin-left: auto; color: #3f51b5; }
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
