<template>
  <div class="vendor_space-y-6">
    <!-- Risk Assessment Matrix -->
    <div class="vendor_card">
      <div class="vendor_card-header">
        <h3 class="vendor_card-title">Risk Assessment Matrix</h3>
      </div>
      <div class="vendor_card-content">
        <div class="vendor_risk-matrix-container">
          <!-- Matrix Grid -->
          <div class="vendor_risk-matrix">
            <!-- Header row with likelihood labels -->
            <div class="vendor_risk-cell vendor_risk-cell-header"></div>
            <div class="vendor_risk-cell vendor_risk-cell-header">1</div>
            <div class="vendor_risk-cell vendor_risk-cell-header">2</div>
            <div class="vendor_risk-cell vendor_risk-cell-header">3</div>
            <div class="vendor_risk-cell vendor_risk-cell-header">4</div>
            <div class="vendor_risk-cell vendor_risk-cell-header">5</div>
            
            <!-- Impact 5 row -->
            <div class="vendor_risk-cell vendor_risk-cell-header">5</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">5</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">10</div>
            <div class="vendor_risk-cell vendor_risk-cell--high">15</div>
            <div class="vendor_risk-cell vendor_risk-cell--critical">20</div>
            <div class="vendor_risk-cell vendor_risk-cell--critical">25</div>
            
            <!-- Impact 4 row -->
            <div class="vendor_risk-cell vendor_risk-cell-header">4</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">4</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">8</div>
            <div class="vendor_risk-cell vendor_risk-cell--high">12</div>
            <div class="vendor_risk-cell vendor_risk-cell--critical">16</div>
            <div class="vendor_risk-cell vendor_risk-cell--critical">20</div>
            
            <!-- Impact 3 row -->
            <div class="vendor_risk-cell vendor_risk-cell-header">3</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">3</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">6</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">9</div>
            <div class="vendor_risk-cell vendor_risk-cell--high">12</div>
            <div class="vendor_risk-cell vendor_risk-cell--high">15</div>
            
            <!-- Impact 2 row -->
            <div class="vendor_risk-cell vendor_risk-cell-header">2</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">2</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">4</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">6</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">8</div>
            <div class="vendor_risk-cell vendor_risk-cell--medium">10</div>
            
            <!-- Impact 1 row -->
            <div class="vendor_risk-cell vendor_risk-cell-header">1</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">1</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">2</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">3</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">4</div>
            <div class="vendor_risk-cell vendor_risk-cell--low">5</div>
          </div>
          
          <!-- Matrix Labels -->
          <div class="vendor_flex vendor_justify-between vendor_mt-2 vendor_text-sm vendor_text-muted-foreground">
            <span>← Impact</span>
            <span>Likelihood →</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Current Risk Factors -->
    <div class="vendor_card">
      <div class="vendor_card-header">
        <h3 class="vendor_card-title">Current Risk Factors</h3>
      </div>
      <div class="vendor_card-content">
        <div class="vendor_space-y-4">
          <div v-for="vendor_risk in vendor_risks" :key="vendor_risk.id" class="vendor_flex vendor_items-center vendor_justify-between vendor_p-4 vendor_border vendor_rounded-lg">
            <div>
              <h4 class="vendor_font-medium">{{ vendor_risk.name }}</h4>
              <p class="vendor_text-sm vendor_text-muted-foreground">
                Impact: {{ vendor_risk.impact }}, Likelihood: {{ vendor_risk.likelihood }}
              </p>
              <p class="vendor_text-xs vendor_text-muted-foreground">
                Score: {{ vendor_risk.impact * vendor_risk.likelihood }}
              </p>
            </div>
            <span class="vendor_badge" :class="vendor_getRiskLevelClass(vendor_risk.level)">
              {{ vendor_risk.level.toUpperCase() }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  vendor_risks: {
    type: Array,
    default: () => []
  }
})

const vendor_getRiskLevelClass = (level) => {
  switch (level) {
    case 'low': return 'vendor_badge-success'
    case 'medium': return 'vendor_badge-warning'
    case 'high': return 'vendor_badge-destructive'
    case 'critical': return 'vendor_badge-destructive'
    default: return 'vendor_badge-default'
  }
}
</script>

<style scoped>
.vendor_risk-matrix-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.vendor_risk-matrix {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 2px;
  margin: 20px 0;
}

.vendor_risk-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  border-radius: 4px;
  min-height: 40px;
}

.vendor_risk-cell-header {
  background: var(--muted);
  color: var(--muted-foreground);
  font-weight: 700;
}

.vendor_risk-cell--low {
  background: rgba(22, 163, 74, 0.2);
  color: var(--success);
}

.vendor_risk-cell--medium {
  background: rgba(245, 158, 11, 0.2);
  color: var(--warning);
}

.vendor_risk-cell--high {
  background: rgba(220, 38, 38, 0.2);
  color: var(--destructive);
}

.vendor_risk-cell--critical {
  background: rgba(220, 38, 38, 0.4);
  color: var(--destructive);
}
</style>
