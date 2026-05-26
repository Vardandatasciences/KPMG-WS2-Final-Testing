<template>
  <div class="entity-tree-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <i class="fas fa-arrow-left"></i> Back
      </button>
      <h1 class="page-title">Entity Hierarchy — {{ tenantName }}</h1>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading tree...</div>
    <div v-else-if="error" class="error-state"><i class="fas fa-exclamation-circle"></i> {{ error }}</div>

    <div v-else class="tree-wrapper">
      <div v-if="!tree.length" class="empty-state">
        <i class="fas fa-sitemap fa-3x"></i>
        <p>No entity hierarchy found for this tenant</p>
      </div>
      <div v-else class="tree-container">
        <TreeNode
          v-for="node in tree"
          :key="node.id"
          :node="node"
          :depth="0"
        />
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'

const TreeNode = {
  name: 'TreeNode',
  props: {
    node: { type: Object, required: true },
    depth: { type: Number, default: 0 },
  },
  data() {
    return { expanded: true }
  },
  template: `
    <div class="tree-node" :style="{ paddingLeft: depth * 24 + 'px' }">
      <div class="node-row" :class="'node-type-' + node.type">
        <button v-if="hasChildren" class="expand-btn" @click="expanded = !expanded">
          <i :class="expanded ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
        </button>
        <span v-else class="expand-placeholder"></span>
        <i :class="nodeIcon"></i>
        <span class="node-name">{{ node.name }}</span>
        <span class="node-code" v-if="node.code">{{ node.code }}</span>
        <span class="node-type-badge">{{ node.type }}</span>
        <span class="badge" :class="node.status === 'active' ? 'badge-success' : 'badge-neutral'">{{ node.status }}</span>
      </div>
      <div v-if="expanded && hasChildren">
        <TreeNode
          v-for="child in node.children"
          :key="child.id"
          :node="child"
          :depth="depth + 1"
        />
      </div>
    </div>
  `,
  computed: {
    hasChildren() { return this.node.children && this.node.children.length > 0 },
    nodeIcon() {
      const icons = { entity: 'fas fa-building', business_unit: 'fas fa-layer-group', department: 'fas fa-users' }
      return icons[this.node.type] || 'fas fa-circle'
    },
  },
}

export default {
  name: 'EntityTree',
  components: { TreeNode },
  data() {
    return {
      tree: [], loading: false, error: null, tenantName: '',
    }
  },
  mounted() { this.fetchTree() },
  methods: {
    async fetchTree() {
      const tenantId = this.$route.params.tenantId
      this.loading = true; this.error = null
      try {
        const res = await tenantService.getEntityTree(tenantId)
        this.tree = res?.data?.tree ?? res?.data ?? []
        this.tenantName = res?.data?.tenant_name ?? ''
      } catch (e) { this.error = e.message } finally { this.loading = false }
    },
  },
}
</script>

<style scoped>
.entity-tree-page { padding: 24px; margin-left: 236px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 28px; }
.back-btn { background: none; border: 1px solid #ddd; border-radius: 6px; padding: 6px 14px; cursor: pointer; color: #555; font-size: 14px; display: flex; align-items: center; gap: 6px; }
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0; }
.loading-state, .error-state, .empty-state { padding: 60px; text-align: center; color: #aaa; }
.empty-state i { color: #d0d0d0; margin-bottom: 16px; display: block; }
.tree-wrapper { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); padding: 24px; }
</style>

<style>
.tree-node { margin: 2px 0; }
.node-row { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 7px; cursor: default; transition: background 0.15s; font-size: 14px; }
.node-row:hover { background: #f5f7ff; }
.node-type-entity { border-left: 3px solid #3f51b5; }
.node-type-business_unit { border-left: 3px solid #00bcd4; }
.node-type-department { border-left: 3px solid #4caf50; }
.expand-btn { background: none; border: none; cursor: pointer; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; color: #777; font-size: 11px; }
.expand-placeholder { width: 20px; height: 20px; }
.node-name { font-weight: 600; color: #333; }
.node-code { font-size: 11px; background: #f0f0f0; padding: 1px 6px; border-radius: 4px; font-family: monospace; color: #666; }
.node-type-badge { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #999; }
.badge { padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-neutral { background: #f5f5f5; color: #666; }
</style>
