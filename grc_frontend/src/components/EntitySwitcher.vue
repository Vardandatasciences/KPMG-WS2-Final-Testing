<template>
  <div class="entity-switcher" v-if="isMultiEntity" ref="container">
    <button class="switcher-btn" @click="open = !open" :class="{ active: open }">
      <i class="fas fa-building entity-icon"></i>
      <span class="entity-name">{{ currentEntity?.name || 'All Entities' }}</span>
      <i class="fas fa-chevron-down chevron" :class="{ rotated: open }"></i>
    </button>

    <transition name="dropdown">
      <div v-if="open" class="switcher-dropdown">
        <div class="dropdown-header">Switch Entity</div>
        <div
          class="entity-item"
          :class="{ current: !currentEntity }"
          @click="switchEntity(null)"
        >
          <i class="fas fa-globe item-icon"></i>
          <div class="item-info">
            <div class="item-name">All Entities</div>
            <div class="item-sub">Cross-entity view</div>
          </div>
          <i v-if="!currentEntity" class="fas fa-check check-icon"></i>
        </div>
        <div
          v-for="entity in allowedEntities"
          :key="entity.id"
          class="entity-item"
          :class="{ current: entity.id === currentEntity?.id }"
          @click="switchEntity(entity)"
        >
          <i class="fas fa-building item-icon"></i>
          <div class="item-info">
            <div class="item-name">{{ entity.name }}</div>
            <div class="item-sub">{{ entity.entity_type || entity.code }}</div>
          </div>
          <i v-if="entity.id === currentEntity?.id" class="fas fa-check check-icon"></i>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { useTenantStore } from '@/stores/tenant.js'

export default {
  name: 'EntitySwitcher',
  data() {
    return {
      open: false,
      tenantStore: null,
    }
  },
  computed: {
    currentEntity() { return this.tenantStore?.currentEntity },
    allowedEntities() { return this.tenantStore?.allowedEntities ?? [] },
    isMultiEntity() { return this.allowedEntities.length > 1 },
  },
  mounted() {
    this.tenantStore = useTenantStore()
    document.addEventListener('click', this.handleOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  methods: {
    switchEntity(entity) {
      if (entity) {
        this.tenantStore.switchEntity(entity.id)
      } else {
        this.tenantStore.currentEntity = null
        localStorage.removeItem('selected_entity_id')
      }
      this.open = false
      this.$emit('entity-changed', entity)
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
.entity-switcher { position: relative; }
.switcher-btn { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px 12px; cursor: pointer; color: inherit; font-size: 14px; font-weight: 500; transition: background 0.15s; }
.switcher-btn:hover, .switcher-btn.active { background: rgba(255,255,255,0.18); }
.entity-icon { font-size: 13px; opacity: 0.85; }
.entity-name { max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chevron { font-size: 10px; transition: transform 0.2s; }
.chevron.rotated { transform: rotate(180deg); }
.switcher-dropdown { position: absolute; top: calc(100% + 8px); left: 0; min-width: 210px; background: #fff; border-radius: 10px; box-shadow: 0 4px 24px rgba(0,0,0,0.15); z-index: 2000; overflow: hidden; }
.dropdown-header { padding: 10px 14px; font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.7px; border-bottom: 1px solid #f0f0f0; }
.entity-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; transition: background 0.15s; }
.entity-item:hover { background: #f5f7ff; }
.entity-item.current { background: #f0f4ff; }
.item-icon { color: #3f51b5; width: 16px; flex-shrink: 0; }
.item-name { font-size: 14px; font-weight: 600; color: #333; }
.item-sub { font-size: 12px; color: #888; text-transform: capitalize; }
.check-icon { margin-left: auto; color: #3f51b5; font-size: 12px; }
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
