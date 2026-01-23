<template>
  <div class="basel-kpi-dashboard-wrapper">
    <!-- Loading Indicator -->
    <div v-if="loading" class="basel-kpi-loading">
      <i class="fas fa-spinner fa-spin"></i>
      Loading Basel KPIs...
    </div>

    <!-- Header Section -->
    <div v-if="!loading" class="basel-kpi-header">
      <h2 class="basel-kpi-title">Basel KPIs Dashboard</h2>
      <p class="basel-kpi-subtitle">Regulatory Capital and Risk Management Metrics</p>
    </div>

    <!-- Capital Adequacy Section -->
    <div v-if="!loading" class="basel-kpi-section">
      <h3 class="basel-kpi-section-title">Capital Adequacy Ratios</h3>
      <div class="basel-kpi-row">
        <!-- CET1 Ratio -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Common Equity Tier 1 (CET1) Ratio</h3>
          </div>
          <div class="basel-kpi-gauge-container">
            <BaselGauge :value="kpis.cet1.value" :max="kpis.cet1.max" :use-gradient="false" :color="getGaugeColor(kpis.cet1.value, kpis.cet1.threshold)" :display-text="`${kpis.cet1.value}%`" :subtitle="`Target: ${kpis.cet1.threshold}%`"/>
            <div class="basel-kpi-trend-mini">
              <svg viewBox="0 0 150 40" class="basel-kpi-trend-svg">
                <path :d="getTrendPath(kpis.cet1.trend.map(t => t.value || t))" :stroke="convertColorForColorblind('#3498db')" stroke-width="3" fill="none"/>
                <circle v-for="(point, index) in getTrendPoints(kpis.cet1.trend)" 
                        :key="index" :cx="point.x" :cy="point.y" r="3" :fill="convertColorForColorblind('#3498db')"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- S34 Profitability vs Risk-Adjusted Capital -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Profitability vs Risk-Adjusted Capital</h3>
          </div>
          <div class="basel-kpi-bubble-wrap">
            <svg viewBox="0 0 240 120" class="basel-kpi-bubble-svg">
              <circle v-for="(b, i) in kpis.profitVsCapital" :key="i" :cx="b.x" :cy="b.y" :r="b.r" :fill="convertColorForColorblind(b.color)" opacity="0.8" />
            </svg>
            <div class="basel-kpi-bubble-legend">
              <span v-for="(b, i) in kpis.profitVsCapital" :key="'lg-'+i" class="basel-kpi-legend-item"><span class="basel-kpi-legend-dot" :style="{background: convertColorForColorblind(b.color)}"></span>{{ b.name }}</span>
            </div>
          </div>
        </div>

        <!-- S39 Capital Shortfall under Stress -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Capital Shortfall under Stress</h3>
          </div>
          <div class="basel-kpi-waterfall-and-metric">
            <svg viewBox="0 0 260 120" class="basel-kpi-waterfall-svg">
              <rect x="10" y="70" width="60" height="40" :fill="convertColorForColorblind('#60a5fa')" />
              <rect x="80" y="40" width="60" height="70" :fill="convertColorForColorblind('#f59e0b')" />
              <rect x="150" y="30" width="60" height="80" :fill="convertColorForColorblind(kpis.capitalShortfall.shortfall > 0 ? '#ef4444' : '#22c55e')" />
              <line x1="0" y1="110" x2="260" y2="110" stroke="#cbd5e1" stroke-width="1" />
            </svg>
            <div class="basel-kpi-shortfall-metric">Shortfall: ${{ kpis.capitalShortfall.shortfall }}M</div>
          </div>
        </div>

        <!-- S40 Top 10 Counterparty Exposures -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Top Counterparty Exposures</h3>
          </div>
          <div class="basel-kpi-ranked-table">
            <div class="basel-kpi-table-row basel-kpi-table-head">
              <span>Counterparty</span><span>Exposure</span><span>% of Tier1</span>
            </div>
            <div class="basel-kpi-table-row" v-for="(cp, i) in kpis.topCounterparties" :key="i">
              <span>{{ cp.name }}</span>
              <span>${{ cp.exposure }}M</span>
              <div class="basel-kpi-ranked-bar">
                <div class="basel-kpi-ranked-fill" :style="{ width: Math.min(cp.pctTier1, 100) + '%', background: convertColorForColorblind(cp.pctTier1 > 25 ? '#ef4444' : '#10b981') }"></div>
                <span class="basel-kpi-ranked-value">{{ cp.pctTier1 }}%</span>
              </div>
            </div>
          </div>
        </div>
         <!-- Tier 1 Capital Ratio -->
         <div class="global-dashboard-chart-card basel-kpi-card">
           <div class="global-dashboard-chart-header">
             <h3 class="global-dashboard-chart-title">Tier 1 Capital Ratio</h3>
           </div>
           <div class="basel-kpi-gauge-container">
            <BaselGauge :value="kpis.tier1.value" :max="kpis.tier1.max" :use-gradient="false" :color="getGaugeColor(kpis.tier1.value, kpis.tier1.threshold)" :display-text="`${kpis.tier1.value}%`" :subtitle="`Target: ${kpis.tier1.threshold}%`"/>
            <div class="basel-kpi-trend-mini">
              <svg viewBox="0 0 150 40" class="basel-kpi-trend-svg">
                <path :d="getTrendPath(kpis.tier1.trend.map(t => t.value || t))" :stroke="convertColorForColorblind('#2ecc71')" stroke-width="3" fill="none"/>
                <circle v-for="(point, index) in getTrendPoints(kpis.tier1.trend)" 
                        :key="index" :cx="point.x" :cy="point.y" r="3" :fill="convertColorForColorblind('#2ecc71')"/>
              </svg>
            </div>
          </div>
        </div>

         <!-- Total Capital Ratio -->
         <div class="global-dashboard-chart-card basel-kpi-card">
           <div class="global-dashboard-chart-header">
             <h3 class="global-dashboard-chart-title">Total Capital Ratio (CAR)</h3>
           </div>
           <div class="basel-kpi-gauge-container">
            <BaselGauge :value="kpis.totalCapital.value" :max="kpis.totalCapital.max" :use-gradient="false" :color="getGaugeColor(kpis.totalCapital.value, kpis.totalCapital.threshold)" :display-text="`${kpis.totalCapital.value}%`" :subtitle="`Target: ${kpis.totalCapital.threshold}%`"/>
            <div class="basel-kpi-trend-mini">
              <svg viewBox="0 0 150 40" class="basel-kpi-trend-svg">
                <path :d="getTrendPath(kpis.totalCapital.trend.map(t => t.value || t))" :stroke="convertColorForColorblind('#9b59b6')" stroke-width="3" fill="none"/>
                <circle v-for="(point, index) in getTrendPoints(kpis.totalCapital.trend)" 
                        :key="index" :cx="point.x" :cy="point.y" r="3" :fill="convertColorForColorblind('#9b59b6')"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Liquidity Section -->
    <div v-if="!loading" class="basel-kpi-section">
      <h3 class="basel-kpi-section-title">Liquidity Ratios</h3>
      <div class="basel-kpi-row">
         <!-- Leverage Ratio -->
         <div class="global-dashboard-chart-card basel-kpi-card">
           <div class="global-dashboard-chart-header">
             <h3 class="global-dashboard-chart-title">Leverage Ratio</h3>
           </div>
           <div class="basel-kpi-gauge-container">
            <BaselGauge :value="kpis.leverage.value" :max="kpis.leverage.max" :color-start="'#10b981'" :color-end="'#059669'" :display-text="`${kpis.leverage.value}%`" :subtitle="`Min: ${kpis.leverage.threshold}%`"/>
            <div class="basel-kpi-exposure-breakdown">
              <div class="basel-kpi-exposure-item">
                <span class="basel-kpi-exposure-label">On-Balance</span>
                <span class="basel-kpi-exposure-value">85%</span>
              </div>
              <div class="basel-kpi-exposure-item">
                <span class="basel-kpi-exposure-label">Off-Balance</span>
                <span class="basel-kpi-exposure-value">12%</span>
              </div>
              <div class="basel-kpi-exposure-item">
                <span class="basel-kpi-exposure-label">Derivatives</span>
                <span class="basel-kpi-exposure-value">3%</span>
              </div>
            </div>
          </div>
        </div>

         <!-- LCR -->
         <div class="global-dashboard-chart-card basel-kpi-card">
           <div class="global-dashboard-chart-header">
             <h3 class="global-dashboard-chart-title">Liquidity Coverage Ratio (LCR)</h3>
           </div>
           <div class="basel-kpi-gauge-container">
            <BaselGauge :value="kpis.lcr.value" :max="kpis.lcr.max" :color-start="'#60a5fa'" :color-end="'#2563eb'" :display-text="`${kpis.lcr.value}%`" :subtitle="`Min: ${kpis.lcr.threshold}%`"/>
            <div class="basel-kpi-donut-composition">
              <svg viewBox="0 0 100 100" class="basel-kpi-donut-svg">
                <circle cx="50" cy="50" r="35" fill="none" stroke="#e0e6ed" stroke-width="10"/>
                <circle cx="50" cy="50" r="35" fill="none" :stroke="convertColorForColorblind('#3498db')" stroke-width="10"
                        :stroke-dasharray="`${kpis.lcr.hqla.level1 * 2.2} ${220 - kpis.lcr.hqla.level1 * 2.2}`"
                        stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
                <circle cx="50" cy="50" r="35" fill="none" :stroke="convertColorForColorblind('#2ecc71')" stroke-width="10"
                        :stroke-dasharray="`${kpis.lcr.hqla.level2a * 2.2} ${220 - kpis.lcr.hqla.level2a * 2.2}`"
                        :stroke-dashoffset="`${-kpis.lcr.hqla.level1 * 2.2}`" transform="rotate(-90 50 50)"/>
                <text x="50" y="55" text-anchor="middle" class="basel-kpi-donut-center">HQLA</text>
              </svg>
              <div class="basel-kpi-hqla-legend">
                <div class="basel-kpi-legend-item">
                  <span class="basel-kpi-legend-dot" style="background: #3498db;"></span>
                  <span>Level 1: {{ kpis.lcr.hqla.level1 }}%</span>
                </div>
                <div class="basel-kpi-legend-item">
                  <span class="basel-kpi-legend-dot" :style="{ background: convertColorForColorblind('#2ecc71') }"></span>
                  <span>Level 2A: {{ kpis.lcr.hqla.level2a }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

         <!-- NSFR -->
         <div class="global-dashboard-chart-card basel-kpi-card">
           <div class="global-dashboard-chart-header">
             <h3 class="global-dashboard-chart-title">Net Stable Funding Ratio (NSFR)</h3>
           </div>
           <div class="basel-kpi-gauge-container">
            <BaselGauge :value="kpis.nsfr.value" :max="kpis.nsfr.max" :color-start="'#34d399'" :color-end="'#10b981'" :display-text="`${kpis.nsfr.value}%`" :subtitle="`Min: ${kpis.nsfr.threshold}%`"/>
            <div class="basel-kpi-asf-rsf">
              <div class="basel-kpi-funding-bar">
                <div class="basel-kpi-funding-label">ASF</div>
                <div class="basel-kpi-funding-progress">
                  <div class="basel-kpi-funding-fill" :style="{ width: '85%', background: convertColorForColorblind('#2ecc71') }"></div>
                </div>
                <div class="basel-kpi-funding-value">85%</div>
              </div>
              <div class="basel-kpi-funding-bar">
                <div class="basel-kpi-funding-label">RSF</div>
                <div class="basel-kpi-funding-progress">
                  <div class="basel-kpi-funding-fill" style="width: 78%; background: #e74c3c;"></div>
                </div>
                <div class="basel-kpi-funding-value">78%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Risk-Weighted Assets Section -->
    <div v-if="!loading" class="basel-kpi-section">
      <h3 class="basel-kpi-section-title">Risk-Weighted Assets</h3>
      <div class="basel-kpi-row">
        <!-- Total RWA -->
        <div class="global-dashboard-chart-card basel-kpi-card basel-kpi-card-wide">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Total Risk-Weighted Assets (RWA)</h3>
          </div>
          <div class="basel-kpi-rwa-container">
            <div class="basel-kpi-rwa-value">
              <span class="basel-kpi-large-number">{{ kpis.totalRWA.value }}</span>
              <span class="basel-kpi-unit">Billion USD</span>
            </div>
            <div class="basel-kpi-stacked-chart">
              <svg viewBox="0 0 400 60" class="basel-kpi-stacked-svg">
                <!-- Credit RWA -->
                <rect x="0" y="20" :width="kpis.rwaBreakdown.credit * 4" height="20" :fill="convertColorForColorblind('#3498db')"/>
                <!-- Market RWA -->
                <rect :x="kpis.rwaBreakdown.credit * 4" y="20" :width="kpis.rwaBreakdown.market * 4" height="20" :fill="convertColorForColorblind('#e74c3c')"/>
                <!-- Operational RWA -->
                <rect :x="(kpis.rwaBreakdown.credit + kpis.rwaBreakdown.market) * 4" y="20" :width="kpis.rwaBreakdown.operational * 4" height="20" :fill="convertColorForColorblind('#f39c12')"/>
              </svg>
              <div class="basel-kpi-rwa-legend">
                <div class="basel-kpi-legend-item">
                  <span class="basel-kpi-legend-dot" style="background: #3498db;"></span>
                  <span>Credit: {{ kpis.rwaBreakdown.credit }}%</span>
                </div>
                <div class="basel-kpi-legend-item">
                  <span class="basel-kpi-legend-dot" style="background: #e74c3c;"></span>
                  <span>Market: {{ kpis.rwaBreakdown.market }}%</span>
                </div>
                <div class="basel-kpi-legend-item">
                  <span class="basel-kpi-legend-dot" style="background: #f39c12;"></span>
                  <span>Operational: {{ kpis.rwaBreakdown.operational }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RWA by Category -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">RWA by Category</h3>
          </div>
          <div class="basel-kpi-donut-large">
            <svg viewBox="0 0 200 200" class="basel-kpi-donut-large-svg">
              <!-- Credit -->
              <circle cx="100" cy="100" r="70" fill="none" :stroke="convertColorForColorblind('#3498db')" stroke-width="25"
                      :stroke-dasharray="`${kpis.rwaBreakdown.credit * 4.4} ${440 - kpis.rwaBreakdown.credit * 4.4}`"
                      stroke-dashoffset="0" transform="rotate(-90 100 100)"/>
              <!-- Market -->
              <circle cx="100" cy="100" r="70" fill="none" :stroke="convertColorForColorblind('#e74c3c')" stroke-width="25"
                      :stroke-dasharray="`${kpis.rwaBreakdown.market * 4.4} ${440 - kpis.rwaBreakdown.market * 4.4}`"
                      :stroke-dashoffset="`${-kpis.rwaBreakdown.credit * 4.4}`" transform="rotate(-90 100 100)"/>
              <!-- Operational -->
              <circle cx="100" cy="100" r="70" fill="none" :stroke="convertColorForColorblind('#f39c12')" stroke-width="25"
                      :stroke-dasharray="`${kpis.rwaBreakdown.operational * 4.4} ${440 - kpis.rwaBreakdown.operational * 4.4}`"
                      :stroke-dashoffset="`${-(kpis.rwaBreakdown.credit + kpis.rwaBreakdown.market) * 4.4}`" transform="rotate(-90 100 100)"/>
              <text x="100" y="105" text-anchor="middle" class="basel-kpi-donut-center-large">RWA</text>
            </svg>
            <div class="basel-kpi-category-values">
              <div class="basel-kpi-category-item">
                <span class="basel-kpi-category-label">Credit Risk</span>
                <span class="basel-kpi-category-amount">${{ (kpis.totalRWA.value * kpis.rwaBreakdown.credit / 100).toFixed(1) }}B</span>
              </div>
              <div class="basel-kpi-category-item">
                <span class="basel-kpi-category-label">Market Risk</span>
                <span class="basel-kpi-category-amount">${{ (kpis.totalRWA.value * kpis.rwaBreakdown.market / 100).toFixed(1) }}B</span>
              </div>
              <div class="basel-kpi-category-item">
                <span class="basel-kpi-category-label">Operational Risk</span>
                <span class="basel-kpi-category-amount">${{ (kpis.totalRWA.value * kpis.rwaBreakdown.operational / 100).toFixed(1) }}B</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Credit Risk Section -->
    <div v-if="!loading" class="basel-kpi-section">
      <h3 class="basel-kpi-section-title">Credit Risk Metrics</h3>
      <div class="basel-kpi-row">
        <!-- PD Heatmap -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Probability of Default (PD) by Rating</h3>
          </div>
          <div class="basel-kpi-heatmap">
            <div class="basel-kpi-heatmap-grid">
              <div v-for="(rating, index) in kpis.pdByRating" :key="index" 
                   class="basel-kpi-heatmap-cell" 
                   :style="{ backgroundColor: getHeatmapColor(rating.pd) }">
                <div class="basel-kpi-rating-label">{{ rating.rating }}</div>
                <div class="basel-kpi-rating-value">{{ rating.pd }}%</div>
              </div>
            </div>
            <div class="basel-kpi-heatmap-scale">
              <span>Low Risk</span>
              <div class="basel-kpi-color-scale">
                <div class="basel-kpi-scale-segment" :style="{ background: convertColorForColorblind('#2ecc71') }"></div>
                <div class="basel-kpi-scale-segment" style="background: #f1c40f;"></div>
                <div class="basel-kpi-scale-segment" style="background: #e67e22;"></div>
                <div class="basel-kpi-scale-segment" style="background: #e74c3c;"></div>
              </div>
              <span>High Risk</span>
            </div>
          </div>
        </div>

        <!-- LGD by Collateral -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Loss Given Default (LGD) by Collateral</h3>
          </div>
          <div class="basel-kpi-bar-chart">
            <div v-for="(item, index) in kpis.lgdByCollateral" :key="index" 
                 class="basel-kpi-bar-item">
              <div class="basel-kpi-bar-label">{{ item.type }}</div>
              <div class="basel-kpi-bar-track">
                <div class="basel-kpi-bar-fill" 
                     :style="{ width: item.lgd + '%', backgroundColor: getBarColor(index) }"></div>
              </div>
              <div class="basel-kpi-bar-value">{{ item.lgd }}%</div>
            </div>
            <div class="basel-kpi-trend-small">
               <svg viewBox="0 0 200 50" class="basel-kpi-trend-small-svg">
                 <path :d="getTrendPath(kpis.lgdTrend)" :stroke="convertColorForColorblind('#e74c3c')" stroke-width="3" :fill="convertColorForColorblind('rgba(231, 76, 60, 0.1)')"/>
              </svg>
              <div class="basel-kpi-trend-label">6-Month LGD Trend</div>
            </div>
          </div>
        </div>

        <!-- Expected Loss -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Expected Loss (EL)</h3>
          </div>
          <div class="basel-kpi-el-container">
            <div class="basel-kpi-el-value">
              <span class="basel-kpi-large-number">{{ kpis.expectedLoss.value }}</span>
              <span class="basel-kpi-unit">Million USD</span>
            </div>
            <div class="basel-kpi-el-components">
              <div class="basel-kpi-component-stack">
                <div class="basel-kpi-component-item">
                  <span class="basel-kpi-component-label">PD Component</span>
                  <div class="basel-kpi-component-bar">
                    <div class="basel-kpi-component-fill" style="width: 35%; background: #3498db;"></div>
                  </div>
                  <span class="basel-kpi-component-value">35%</span>
                </div>
                <div class="basel-kpi-component-item">
                  <span class="basel-kpi-component-label">LGD Component</span>
                  <div class="basel-kpi-component-bar">
                    <div class="basel-kpi-component-fill" style="width: 28%; background: #e74c3c;"></div>
                  </div>
                  <span class="basel-kpi-component-value">28%</span>
                </div>
                <div class="basel-kpi-component-item">
                  <span class="basel-kpi-component-label">EAD Component</span>
                  <div class="basel-kpi-component-bar">
                    <div class="basel-kpi-component-fill" style="width: 37%; background: #f39c12;"></div>
                  </div>
                  <span class="basel-kpi-component-value">37%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Asset Quality Section -->
    <div v-if="!loading" class="basel-kpi-section">
      <h3 class="basel-kpi-section-title">Asset Quality</h3>
      <div class="basel-kpi-row">
        <!-- NPL Ratio -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Non-Performing Loan (NPL) Ratio</h3>
          </div>
          <div class="basel-kpi-npl-container">
            <div class="basel-kpi-npl-value">
              <span class="basel-kpi-large-number">{{ kpis.nplRatio.value }}%</span>
            </div>
            <div class="basel-kpi-trend-area">
              <svg viewBox="0 0 300 80" class="basel-kpi-trend-area-svg">
                <defs>
                  <linearGradient :id="'nplGradient-' + (colorblindMode || 'normal')" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" :style="`stop-color:${convertColorForColorblind('#e74c3c')};stop-opacity:0.3`" />
                    <stop offset="100%" :style="`stop-color:${convertColorForColorblind('#e74c3c')};stop-opacity:0.1`" />
                  </linearGradient>
                </defs>
                <path :d="getAreaPath(kpis.nplRatio.trend)" :fill="`url(#nplGradient-${colorblindMode || 'normal'})`" :stroke="convertColorForColorblind('#e74c3c')" stroke-width="2"/>
              </svg>
            </div>
            <div class="basel-kpi-npl-breakdown">
              <div v-for="(product, index) in kpis.nplByProduct" :key="index" 
                   class="basel-kpi-product-item">
                <span class="basel-kpi-product-label">{{ product.name }}</span>
                <span class="basel-kpi-product-value">{{ product.npl }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Market Risk VaR -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Value at Risk (VaR, 99%)</h3>
          </div>
          <div class="basel-kpi-var-container">
            <div class="basel-kpi-var-current">
              <span class="basel-kpi-large-number">{{ kpis.var.current }}</span>
              <span class="basel-kpi-unit">Million USD</span>
            </div>
            <div class="basel-kpi-var-chart">
              <svg viewBox="0 0 300 100" class="basel-kpi-var-svg">
                <defs>
                  <linearGradient :id="'varGradient-' + (colorblindMode || 'normal')" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" :style="`stop-color:${convertColorForColorblind('#9b59b6')};stop-opacity:0.4`" />
                    <stop offset="100%" :style="`stop-color:${convertColorForColorblind('#9b59b6')};stop-opacity:0.1`" />
                  </linearGradient>
                </defs>
                <path :d="getAreaPath(kpis.var.timeSeries)" :fill="`url(#varGradient-${colorblindMode || 'normal'})`" :stroke="convertColorForColorblind('#9b59b6')" stroke-width="3"/>
                <line :x1="kpis.var.limit * 3" y1="0" :x2="kpis.var.limit * 3" y2="100" :stroke="convertColorForColorblind('#e74c3c')" stroke-width="2" stroke-dasharray="5,5"/>
                <text :x="kpis.var.limit * 3 + 5" y="15" class="basel-kpi-limit-label">Limit</text>
              </svg>
            </div>
          </div>
        </div>

        <!-- Operational Risk -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Operational Risk - Business Indicator</h3>
          </div>
          <div class="basel-kpi-op-risk-container">
            <div class="basel-kpi-bi-gauge">
              <BaselGauge :value="kpis.operationalRisk.biValue" :max="3000" :color-start="'#fbbf24'" :color-end="'#f59e0b'" :display-text="`$${kpis.operationalRisk.biValue}M`" :subtitle="`Bucket ${kpis.operationalRisk.bucket}`"/>
            </div>
            <div class="basel-kpi-bi-components">
              <div v-for="(component, index) in kpis.operationalRisk.components" :key="index" 
                   class="basel-kpi-bi-component">
                <div class="basel-kpi-bi-label">{{ component.name }}</div>
                <div class="basel-kpi-bi-bar">
                  <div class="basel-kpi-bi-fill" 
                       :style="{ width: (component.value / kpis.operationalRisk.biValue * 100) + '%', backgroundColor: getBarColor(index) }"></div>
                </div>
                <div class="basel-kpi-bi-value">${{ component.value }}M</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Additional Risk Metrics -->
    <div v-if="!loading" class="basel-kpi-section">
      <h3 class="basel-kpi-section-title">Additional Risk Metrics</h3>
      <div class="basel-kpi-row">
        <!-- S29 Liquidity Stress Test Results -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Liquidity Stress Test Results</h3>
          </div>
          <div class="basel-kpi-waterfall-and-table">
            <div class="basel-kpi-waterfall">
              <svg viewBox="0 0 260 120" class="basel-kpi-waterfall-svg">
                <rect x="10" y="70" width="50" height="40" :fill="convertColorForColorblind('#60a5fa')" />
                <rect x="70" y="55" width="50" height="55" :fill="convertColorForColorblind('#22c55e')" />
                <rect x="130" y="35" width="50" height="75" :fill="convertColorForColorblind('#f59e0b')" />
                <rect x="190" y="20" width="50" height="90" :fill="convertColorForColorblind(kpis.stress.lcrSevere >= 100 ? '#22c55e' : '#ef4444')" />
                <line x1="0" y1="110" x2="260" y2="110" stroke="#cbd5e1" stroke-width="1" />
                <text x="215" y="18" text-anchor="middle" class="basel-kpi-waterfall-label">Severe</text>
              </svg>
            </div>
            <div class="basel-kpi-simple-table">
              <div class="basel-kpi-table-row basel-kpi-table-head">
                <span>Scenario</span><span>LCR %</span><span>Cash Shortfall</span>
              </div>
              <div class="basel-kpi-table-row" v-for="row in kpis.stress.table" :key="row.name">
                <span>{{ row.name }}</span>
                <span :class="{'basel-kpi-text-danger': row.lcr < 100, 'basel-kpi-text-success': row.lcr >= 100}">{{ row.lcr }}</span>
                <span>{{ row.shortfall }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- S30 Large Exposure Limits -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Large Exposure Limits (% of Tier1)</h3>
          </div>
          <div class="basel-kpi-ranked-table">
            <div class="basel-kpi-table-row basel-kpi-table-head">
              <span>Counterparty</span><span>% of Tier1</span>
            </div>
            <div class="basel-kpi-table-row" v-for="(item, i) in kpis.largeExposures" :key="i">
              <span>{{ item.name }}</span>
              <div class="basel-kpi-ranked-bar">
                <div class="basel-kpi-ranked-fill" :style="{ width: Math.min(item.pct, 100) + '%', background: convertColorForColorblind(item.pct > 25 ? '#ef4444' : '#10b981') }"></div>
                <span class="basel-kpi-ranked-value">{{ item.pct }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- S31 Funding Concentration Risk -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Funding Concentration Risk</h3>
          </div>
          <div class="basel-kpi-mini-heatmap">
            <div class="basel-kpi-mini-heatmap-grid">
              <div class="basel-kpi-mini-heatmap-cell" v-for="(c, i) in kpis.fundingConcentration" :key="i" :style="{ background: getHeatmapColor(c.pct) }">
                <span class="basel-kpi-mini-heatmap-label">{{ c.name }}</span>
                <span class="basel-kpi-mini-heatmap-value">{{ c.pct }}%</span>
              </div>
            </div>
            <div class="basel-kpi-mini-note">Alert if Top 3 &gt; {{ kpis.fundingTop3Threshold }}%</div>
          </div>
        </div>

        <!-- S32 Recovery Plan Viability -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Recovery Plan Viability</h3>
          </div>
          <div class="basel-kpi-radar-wrap">
            <svg viewBox="0 0 150 120" class="basel-kpi-radar-svg">
              <polygon points="75,15 135,60 110,110 40,110 15,60" fill="none" stroke="#cbd5e1" />
              <polygon :points="kpis.recovery.radarPoints" :fill="convertColorForColorblind('rgba(34,197,94,0.25)')" :stroke="convertColorForColorblind('#22c55e')" />
              <text x="75" y="105" text-anchor="middle" class="basel-kpi-radar-score">Score: {{ kpis.recovery.score }}</text>
            </svg>
            <div class="basel-kpi-radar-status" :class="{ 'basel-kpi-text-success': kpis.recovery.score >= 75, 'basel-kpi-text-danger': kpis.recovery.score < 75 }">
              {{ kpis.recovery.score >= 75 ? 'PASS' : 'FAIL' }} (≥ 75)
            </div>
          </div>
        </div>

        <!-- S33 Capital Planning Forecast Accuracy -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Capital Planning Forecast Accuracy</h3>
          </div>
          <div class="basel-kpi-scatter-wrap">
            <svg viewBox="0 0 220 120" class="basel-kpi-scatter-svg">
              <line x1="20" y1="100" x2="200" y2="100" stroke="#cbd5e1" />
              <line x1="20" y1="100" x2="20" y2="20" stroke="#cbd5e1" />
              <circle v-for="(p, i) in kpis.mape.points" :key="i" :cx="p.x" :cy="p.y" r="3" :fill="convertColorForColorblind('#3b82f6')" />
            </svg>
            <div class="basel-kpi-metric">MAPE: {{ kpis.mape.value }}% (Target ≤ 2%)</div>
          </div>
        </div>
        <!-- Interest Rate Risk -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Interest Rate Risk (ΔEVE)</h3>
          </div>
          <div class="basel-kpi-irrbb-container">
            <div class="basel-kpi-scenario-table">
              <div class="basel-kpi-scenario-header">
                <span>Scenario</span>
                <span>ΔEVE</span>
                <span>% of Tier1</span>
              </div>
              <div v-for="(scenario, index) in kpis.interestRateRisk.scenarios" :key="index" 
                   class="basel-kpi-scenario-row" 
                   :class="{ 'basel-kpi-scenario-breach': scenario.tier1Pct > 15 }">
                <span>{{ scenario.name }}</span>
                <span>${{ scenario.deve }}M</span>
                <span>{{ scenario.tier1Pct }}%</span>
              </div>
            </div>
            <div class="basel-kpi-sensitivity-chart">
              <svg viewBox="0 0 250 80" class="basel-kpi-sensitivity-svg">
                <line x1="125" y1="10" x2="125" y2="70" stroke="#bdc3c7" stroke-width="1"/>
                <line x1="20" y1="40" x2="230" y2="40" stroke="#bdc3c7" stroke-width="1"/>
                <circle v-for="(point, index) in kpis.interestRateRisk.sensitivityPoints" :key="index"
                        :cx="point.x" :cy="point.y" r="4" 
                        :fill="point.y < 40 ? '#2ecc71' : '#e74c3c'"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- FX Exposure -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Foreign Exchange Exposure</h3>
          </div>
          <div class="basel-kpi-fx-container">
            <div class="basel-kpi-fx-table">
              <div class="basel-kpi-fx-header">
                <span>Currency</span>
                <span>Exposure</span>
                <span>Limit</span>
              </div>
              <div v-for="(currency, index) in kpis.fxExposure.currencies" :key="index" 
                   class="basel-kpi-fx-row">
                <span class="basel-kpi-currency-code">{{ currency.code }}</span>
                <span>${{ currency.exposure }}M</span>
                <span>${{ currency.limit }}M</span>
              </div>
            </div>
            <div class="basel-kpi-world-map">
              <svg viewBox="0 0 300 150" class="basel-kpi-map-svg">
                <!-- Simplified world map with exposure indicators -->
                <circle cx="80" cy="60" r="8" :fill="convertColorForColorblind('#3498db')" opacity="0.7"/> <!-- EUR -->
                <circle cx="120" cy="80" r="6" :fill="convertColorForColorblind('#e74c3c')" opacity="0.7"/> <!-- GBP -->
                <circle cx="200" cy="50" r="5" :fill="convertColorForColorblind('#f39c12')" opacity="0.7"/> <!-- JPY -->
                <circle cx="50" cy="90" r="4" :fill="convertColorForColorblind('#2ecc71')" opacity="0.7"/> <!-- CAD -->
                <text x="20" y="140" class="basel-kpi-map-label">FX Exposure by Region</text>
              </svg>
            </div>
          </div>
        </div>

        <!-- Internal Loss Multiplier -->
        <div class="global-dashboard-chart-card basel-kpi-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">Internal Loss Multiplier (ILM)</h3>
          </div>
          <div class="basel-kpi-ilm-container">
            <div class="basel-kpi-ilm-gauge">
               <BaselGauge :value="kpis.ilm.value" :max="kpis.ilm.max" :color-start="'#c4b5fd'" :color-end="'#a78bfa'" :display-text="`${kpis.ilm.value}`" subtitle="Target: ≤ 1.0"/>
            </div>
            <div class="basel-kpi-ilm-trend">
              <svg viewBox="0 0 200 60" class="basel-kpi-trend-svg">
                <path :d="getTrendPath(kpis.ilm.trend)" :stroke="convertColorForColorblind('#9b59b6')" stroke-width="3" fill="none"/>
                <circle v-for="(point, index) in getTrendPoints(kpis.ilm.trend)" 
                        :key="index" :cx="point.x" :cy="point.y" r="3" :fill="convertColorForColorblind('#9b59b6')"/>
              </svg>
              <div class="basel-kpi-trend-label">12-Month ILM Trend</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import './baselkpi.css';
import BaselGauge from './BaselGauge.vue';
import { convertColorForColorblind as convertColorFromUtil } from '@/utils/colorblindness';

export default {
  name: 'BaselKPI',
  components: { BaselGauge },
  data() {
    return {
      loading: false,
      colorblindMode: null,
      colorblindObserver: null,
      kpis: {
        cet1: {
          value: 11.2,
          threshold: 10.0,
          max: 15.0,
          trend: [10.8, 10.9, 11.1, 11.0, 11.3, 11.2]
        },
        tier1: {
          value: 12.5,
          threshold: 8.5,
          max: 15.0,
          trend: [12.1, 12.3, 12.4, 12.2, 12.6, 12.5]
        },
        totalCapital: {
          value: 15.8,
          threshold: 12.0,
          max: 20.0,
          trend: [15.2, 15.4, 15.6, 15.5, 15.9, 15.8]
        },
        leverage: {
          value: 4.2,
          threshold: 3.0,
          max: 6.0,
          trend: [4.0, 4.1, 4.2, 4.1, 4.3, 4.2]
        },
        lcr: {
          value: 125,
          threshold: 100,
          max: 150,
          trend: [120, 122, 125, 123, 127, 125],
          hqla: {
            level1: 75,
            level2a: 20,
            level2b: 5
          }
        },
        nsfr: {
          value: 108,
          threshold: 100,
          max: 120,
          trend: [105, 106, 108, 107, 109, 108]
        },
        totalRWA: {
          value: 485.2
        },
        rwaBreakdown: {
          credit: 78,
          market: 12,
          operational: 10
        },
        pdByRating: [
          { rating: 'AAA', pd: 0.02 },
          { rating: 'AA', pd: 0.05 },
          { rating: 'A', pd: 0.12 },
          { rating: 'BBB', pd: 0.28 },
          { rating: 'BB', pd: 0.85 },
          { rating: 'B', pd: 2.45 },
          { rating: 'CCC', pd: 8.20 },
          { rating: 'D', pd: 100 }
        ],
        lgdByCollateral: [
          { type: 'Secured Real Estate', lgd: 25 },
          { type: 'Corporate Guarantees', lgd: 45 },
          { type: 'Cash Collateral', lgd: 5 },
          { type: 'Unsecured', lgd: 65 },
          { type: 'Subordinated', lgd: 85 }
        ],
        lgdTrend: [42, 44, 43, 45, 44, 43],
        expectedLoss: {
          value: 325.4
        },
        nplRatio: {
          value: 2.8,
          trend: [3.2, 3.1, 2.9, 2.8, 2.7, 2.8]
        },
        nplByProduct: [
          { name: 'Retail Mortgages', npl: 1.2 },
          { name: 'Corporate Loans', npl: 3.8 },
          { name: 'SME Lending', npl: 4.5 },
          { name: 'Credit Cards', npl: 2.1 }
        ],
        var: {
          current: 45.8,
          limit: 75,
          timeSeries: [42, 45, 48, 46, 44, 45.8]
        },
        operationalRisk: {
          biValue: 2450,
          bucket: 3,
          components: [
            { name: 'Interest Income', value: 1200 },
            { name: 'Fee Income', value: 680 },
            { name: 'Trading Income', value: 350 },
            { name: 'Other Income', value: 220 }
          ]
        },
        interestRateRisk: {
          scenarios: [
            { name: '+200bp parallel', deve: -125, tier1Pct: 8.5 },
            { name: '-200bp parallel', deve: +89, tier1Pct: 6.1 },
            { name: 'Steepener', deve: -95, tier1Pct: 6.5 },
            { name: 'Flattener', deve: +45, tier1Pct: 3.1 },
            { name: 'Short shock', deve: -185, tier1Pct: 12.6 }
          ],
          sensitivityPoints: [
            { x: 50, y: 35 },
            { x: 80, y: 45 },
            { x: 125, y: 40 },
            { x: 170, y: 38 },
            { x: 200, y: 50 }
          ]
        },
        stress: {
          lcrSevere: 92,
          table: [
            { name: 'Baseline', lcr: 125, shortfall: '$0M' },
            { name: 'Moderate', lcr: 110, shortfall: '$0M' },
            { name: 'Severe', lcr: 92, shortfall: '$120M' }
          ]
        },
        largeExposures: [
          { name: 'Counterparty A', pct: 18 },
          { name: 'Counterparty B', pct: 22 },
          { name: 'Counterparty C', pct: 27 },
          { name: 'Counterparty D', pct: 12 }
        ],
        fundingTop3Threshold: 40,
        fundingConcentration: [
          { name: 'CP A', pct: 18 },
          { name: 'CP B', pct: 15 },
          { name: 'CP C', pct: 12 },
          { name: 'CP D', pct: 9 },
          { name: 'CP E', pct: 8 }
        ],
        recovery: {
          score: 78,
          radarPoints: '75,25 120,60 100,100 45,100 30,60'
        },
        mape: {
          value: 1.6,
          points: [ {x:40,y:90},{x:60,y:80},{x:80,y:85},{x:110,y:70},{x:140,y:65},{x:170,y:60} ]
        },
        profitVsCapital: [
          { name: 'BU1', x: 50, y: 80, r: 10, color: '#60a5fa' },
          { name: 'BU2', x: 90, y: 60, r: 14, color: '#34d399' },
          { name: 'BU3', x: 130, y: 50, r: 12, color: '#f59e0b' },
          { name: 'BU4', x: 170, y: 40, r: 16, color: '#a78bfa' }
        ],
        capitalShortfall: {
          shortfall: 280
        },
        topCounterparties: [
          { name: 'CP A', exposure: 820, pctTier1: 18 },
          { name: 'CP B', exposure: 950, pctTier1: 23 },
          { name: 'CP C', exposure: 1200, pctTier1: 29 },
          { name: 'CP D', exposure: 600, pctTier1: 15 }
        ],
        fxExposure: {
          currencies: [
            { code: 'EUR', exposure: 2850, limit: 3000 },
            { code: 'GBP', exposure: 1240, limit: 1500 },
            { code: 'JPY', exposure: 890, limit: 1200 },
            { code: 'CAD', exposure: 650, limit: 800 },
            { code: 'CHF', exposure: 420, limit: 600 }
          ]
        },
        ilm: {
          value: 0.88,
          max: 1.5,
          trend: [0.92, 0.89, 0.87, 0.88, 0.86, 0.88]
        }
      }
    }
  },
  methods: {
     getGaugeArc(value, max) {
       const percentage = Math.min(value / max, 1);
       const angle = percentage * 180; // 180 degrees for semicircle
       const radians = (angle - 90) * (Math.PI / 180);
       const centerX = 80;
       const centerY = 75;
       const radius = 55;
       const x = centerX + radius * Math.cos(radians);
       const y = centerY + radius * Math.sin(radians);
       const largeArcFlag = angle > 180 ? 1 : 0;
       return `M 25 75 A 55 55 0 ${largeArcFlag} 1 ${x} ${y}`;
     },
    
    getGaugeColor(value, threshold) {
      if (value >= threshold) return '#2ecc71';
      if (value >= threshold * 0.8) return '#f39c12';
      return '#e74c3c';
    },
    
     getTrendPath(trendData) {
       if (!trendData || trendData.length === 0) return '';
       
       const width = 150;
       const height = 40;
       const padding = 5;
       const xStep = (width - 2 * padding) / (trendData.length - 1);
       const minValue = Math.min(...trendData);
       const maxValue = Math.max(...trendData);
       const range = maxValue - minValue || 1;
      
       let path = '';
       trendData.forEach((value, index) => {
         const x = padding + index * xStep;
         const y = padding + (height - 2 * padding) - ((value - minValue) / range) * (height - 2 * padding);
        if (index === 0) {
          path = `M${x},${y}`;
        } else {
          path += ` L${x},${y}`;
        }
      });
      
      return path;
    },
    
     getTrendPoints(trendData) {
       if (!trendData || trendData.length === 0) return [];
       
       const width = 150;
       const height = 40;
       const padding = 5;
       const xStep = (width - 2 * padding) / (trendData.length - 1);
       const minValue = Math.min(...trendData);
       const maxValue = Math.max(...trendData);
       const range = maxValue - minValue || 1;
       
       return trendData.map((value, index) => ({
         x: padding + index * xStep,
         y: padding + (height - 2 * padding) - ((value - minValue) / range) * (height - 2 * padding)
       }));
    },
    
    getAreaPath(trendData) {
      if (!trendData || trendData.length === 0) return '';
      
      const width = 300;
      const height = 80;
      const xStep = width / (trendData.length - 1);
      const minValue = Math.min(...trendData);
      const maxValue = Math.max(...trendData);
      const range = maxValue - minValue || 1;
      
      let path = '';
      trendData.forEach((value, index) => {
        const x = index * xStep;
        const y = height - ((value - minValue) / range) * (height - 10) - 5;
        if (index === 0) {
          path = `M${x},${height} L${x},${y}`;
        } else {
          path += ` L${x},${y}`;
        }
      });
      path += ` L${width},${height} Z`;
      
      return path;
    },
    
    getHeatmapColor(pd) {
      let color;
      if (pd < 0.1) color = '#2ecc71';
      else if (pd < 0.5) color = '#f1c40f';
      else if (pd < 2.0) color = '#e67e22';
      else color = '#e74c3c';
      return this.convertColorForColorblind(color);
    },
    
    getBarColor(index) {
      const colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6', '#1abc9c'];
      const color = colors[index % colors.length];
      return this.convertColorForColorblind(color);
    },
    getColorblindMode() {
      if (typeof document === 'undefined') return null;
      const html = document.documentElement;
      return html.getAttribute('data-colorblind') || null;
    },
    rgbaToHex(rgba) {
      if (!rgba) return rgba;
      if (rgba.startsWith('#')) return rgba.toLowerCase();
      
      const match = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
      if (match) {
        const r = parseInt(match[1]).toString(16).padStart(2, '0');
        const g = parseInt(match[2]).toString(16).padStart(2, '0');
        const b = parseInt(match[3]).toString(16).padStart(2, '0');
        return `#${r}${g}${b}`.toLowerCase();
      }
      return rgba.toLowerCase();
    },
    convertColorForColorblind(color) {
      // Use the shared utility function
      // This ensures all colors come from Colourblindness.css CSS variables
      return convertColorFromUtil(color);
    },
    initColorblindnessTracking() {
      if (typeof document === 'undefined') return;
      
      this.colorblindMode = this.getColorblindMode();
      
      this.colorblindObserver = new MutationObserver(() => {
        const newMode = this.getColorblindMode();
        if (newMode !== this.colorblindMode) {
          this.colorblindMode = newMode;
          this.$forceUpdate(); // Force re-render to update all colors
        }
      });
      
      this.colorblindObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-colorblind']
      });
    }
  },
  mounted() {
    this.initColorblindnessTracking();
  },
  beforeUnmount() {
    if (this.colorblindObserver) {
      this.colorblindObserver.disconnect();
    }
  }
}
</script>

<style scoped>
@import '@/assets/css/DashboardCards.css';
</style>
