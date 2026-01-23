<template>
  <div class="global-dashboard-chart-card" data-chart-component="DashboardChartCard">
    <div class="global-dashboard-chart-header">
      <h3 class="global-dashboard-chart-title">{{ title }}</h3>
      <div class="global-dashboard-chart-icon" :style="{ color: iconColor }">
        <i :class="icon"></i>
      </div>
    </div>
    <div class="global-dashboard-chart-container">
      <div v-if="loading" class="global-dashboard-chart-loading"></div>
      <div v-else-if="error" class="global-dashboard-chart-error">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
      </div>
      <component 
        v-else 
        :is="chartComponent" 
        :data="adjustedChartData" 
        :options="mergedChartOptions"
        :key="`chart-${colorblindMode || 'normal'}-${title}-${chartKey}`"
      />
    </div>
  </div>
</template>

<script>
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { Doughnut, Bar, Line as LineChart } from 'vue-chartjs'
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default {
  name: 'DashboardChartCard',
  components: {
    Doughnut,
    Bar,
    LineChart
  },
  props: {
    title: {
      type: String,
      required: true
    },
    icon: {
      type: String,
      required: true
    },
    iconColor: {
      type: String,
      default: '#4f6cff'
    },
    chartType: {
      type: String,
      required: true,
      validator: (value) => ['doughnut', 'bar', 'line'].includes(value)
    },
    chartData: {
      type: Object,
      required: true
    },
    chartOptions: {
      type: Object,
      default: () => ({})
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  setup(props) {
    // Helper function to convert rgba/rgb to hex
    const rgbaToHex = (rgba) => {
      if (!rgba) return rgba
      if (rgba.startsWith('#')) return rgba.toLowerCase()
      
      // Handle rgba/rgb format
      const match = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/)
      if (match) {
        const r = parseInt(match[1]).toString(16).padStart(2, '0')
        const g = parseInt(match[2]).toString(16).padStart(2, '0')
        const b = parseInt(match[3]).toString(16).padStart(2, '0')
        return `#${r}${g}${b}`.toLowerCase()
      }
      return rgba.toLowerCase()
    }

    // Get CSS variable value from Colourblindness.css
    const getCSSVariable = (varName, fallback = null) => {
      if (typeof document === 'undefined') return fallback
      const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
      return value || fallback
    }

    // Build color mapping dynamically from CSS variables in Colourblindness.css
    const buildColorMap = (mode) => {
      if (!mode) return {}
      
      // Get color values from CSS variables
      const cbPrimary = getCSSVariable('--cb-primary', '#2563eb')
      const cbSuccess = getCSSVariable('--cb-success', '#16a34a')
      const cbError = getCSSVariable('--cb-error', '#dc2626')
      const cbAccentTeal = getCSSVariable('--cb-accent-teal', '#0f766e')
      const cbAccentPurple = getCSSVariable('--cb-accent-purple', '#7c3aed')
      const cbWarning = getCSSVariable('--cb-warning', '#f97316')
      
      // Base color map structure - maps original colors to colorblind-friendly colors
      const baseMap = {
        // Red colors - use error color from CSS or keep original
        '#ef4444': cbError || '#ef4444',
        '#dc2626': cbError || '#dc2626',
        '#f87171': cbError || '#f87171', // Risk/Auditor Dashboard red/pink
        
        // Green colors - use success/teal from CSS based on mode
        '#10b981': mode === 'deuteranopia' ? cbAccentTeal : (cbSuccess || '#10b981'),
        '#16a34a': mode === 'deuteranopia' ? cbAccentTeal : (cbSuccess || '#16a34a'),
        '#4ade80': mode === 'deuteranopia' ? cbAccentTeal : (cbSuccess || '#4ade80'), // Risk/Auditor Dashboard green
        '#34d399': mode === 'deuteranopia' ? cbAccentTeal : (cbSuccess || '#34d399'), // Risk Dashboard teal/green
        '#22c55e': mode === 'deuteranopia' ? cbAccentTeal : (cbSuccess || '#22c55e'), // Auditor Dashboard green
        
        // Blue colors - use primary/purple from CSS based on mode
        '#3b82f6': mode === 'tritanopia' ? cbAccentPurple : (cbPrimary || '#3b82f6'),
        '#4f6cff': mode === 'tritanopia' ? cbAccentPurple : (cbPrimary || '#4f6cff'), // Auditor Dashboard blue
        '#2563eb': mode === 'tritanopia' ? cbAccentPurple : (cbPrimary || '#2563eb'),
        '#60a5fa': mode === 'tritanopia' ? cbAccentPurple : (cbPrimary || '#60a5fa'), // Risk/Auditor Dashboard blue
        '#818cf8': mode === 'tritanopia' ? cbAccentPurple : (cbPrimary || '#818cf8'), // Risk Dashboard purple/blue
        '#06b6d4': mode === 'tritanopia' ? cbAccentPurple : (cbPrimary || '#06b6d4'), // Risk Dashboard cyan
        
        // Orange colors - convert to bright yellow for protanopia/deuteranopia
        '#f59e0b': (mode === 'protanopia' || mode === 'deuteranopia') ? '#ffd700' : (cbWarning || '#f59e0b'), // Auditor Dashboard orange
        '#f97316': (mode === 'protanopia' || mode === 'deuteranopia') ? '#ffd700' : (cbWarning || '#f97316'), // Auditor Dashboard orange
        
        // Yellow colors - convert to orange for tritanopia
        '#fbbf24': mode === 'tritanopia' ? '#ff9800' : '#fbbf24', // Risk/Auditor Dashboard yellow
        '#eab308': mode === 'tritanopia' ? '#ff9800' : '#eab308', // Auditor Dashboard yellow
        
        // Pink colors - convert to magenta for all types
        '#f472b6': '#ff00ff', // Risk Dashboard pink -> magenta
        '#fb7185': '#ff00ff', // Risk Dashboard pink -> magenta
        
        // Purple colors - remain the same
        '#a78bfa': cbAccentPurple || '#a78bfa', // Risk Dashboard purple
        '#8b5cf6': cbAccentPurple || '#8b5cf6' // Risk/Auditor Dashboard purple
      }
      
      return baseMap
    }

    // Get current colorblindness mode
    const getColorblindMode = () => {
      const html = document.documentElement
      return html.getAttribute('data-colorblind') || null
    }

    // Convert color to colorblind-friendly color
    const convertColor = (color, mode) => {
      if (!mode || !color) return color
      
      // Get color map for the specified mode
      const colorMap = buildColorMap(mode)
      if (!colorMap || Object.keys(colorMap).length === 0) return color
      
      // Convert rgba/rgb to hex first
      const hexColor = rgbaToHex(color)
      
      // Check both original and normalized color (case-insensitive)
      const normalizedColor = hexColor.toLowerCase()
      const replacement = colorMap[normalizedColor] || colorMap[color.toLowerCase()] || color
      
      // If original was rgba/rgb, preserve the opacity
      if (color.startsWith('rgba') || color.startsWith('rgb')) {
        const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/)
        if (match && replacement.startsWith('#')) {
          const opacity = match[4] || '1'
          // Convert hex to rgb
          const r = parseInt(replacement.slice(1, 3), 16)
          const g = parseInt(replacement.slice(3, 5), 16)
          const b = parseInt(replacement.slice(5, 7), 16)
          if (color.startsWith('rgba')) {
            return `rgba(${r}, ${g}, ${b}, ${opacity})`
          } else {
            return `rgb(${r}, ${g}, ${b})`
          }
        }
      }
      
      return replacement
    }

    // Convert array of colors
    const convertColorArray = (colors, mode) => {
      if (!Array.isArray(colors)) return colors
      return colors.map(color => convertColor(color, mode))
    }

    // Watch for colorblindness mode changes
    const colorblindMode = ref(getColorblindMode())
    const observer = new MutationObserver(() => {
      const newMode = getColorblindMode()
      if (newMode !== colorblindMode.value) {
        colorblindMode.value = newMode
      }
    })

    onMounted(() => {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-colorblind']
      })
      colorblindMode.value = getColorblindMode()
    })

    onUnmounted(() => {
      observer.disconnect()
    })

    // Force re-render key
    const chartKey = ref(0)

    // Computed property to adjust chart data colors based on colorblindness mode
    const adjustedChartData = computed(() => {
      if (!props.chartData) {
        return props.chartData
      }

      const mode = colorblindMode.value
      const adjustedData = JSON.parse(JSON.stringify(props.chartData)) // Deep clone

      // If no colorblindness mode, return original data
      if (!mode) {
        return adjustedData
      }

      if (adjustedData.datasets && Array.isArray(adjustedData.datasets)) {
        adjustedData.datasets.forEach((dataset, datasetIndex) => {
          // Adjust backgroundColor
          if (dataset.backgroundColor) {
            if (Array.isArray(dataset.backgroundColor)) {
              const originalColors = [...dataset.backgroundColor]
              dataset.backgroundColor = convertColorArray(dataset.backgroundColor, mode)
              // Debug log for first dataset
              if (datasetIndex === 0 && originalColors.length > 0) {
                console.log(`[DashboardChartCard] Converting backgroundColor array for ${mode}:`, {
                  original: originalColors.slice(0, 3),
                  converted: dataset.backgroundColor.slice(0, 3)
                })
              }
            } else {
              const originalColor = dataset.backgroundColor
              dataset.backgroundColor = convertColor(dataset.backgroundColor, mode)
              // Debug log for first dataset
              if (datasetIndex === 0) {
                console.log(`[DashboardChartCard] Converting backgroundColor for ${mode}:`, {
                  original: originalColor,
                  converted: dataset.backgroundColor
                })
              }
            }
          }

          // Adjust borderColor
          if (dataset.borderColor) {
            if (Array.isArray(dataset.borderColor)) {
              dataset.borderColor = convertColorArray(dataset.borderColor, mode)
            } else {
              const originalColor = dataset.borderColor
              dataset.borderColor = convertColor(dataset.borderColor, mode)
              // Debug log for first dataset
              if (datasetIndex === 0 && originalColor) {
                console.log(`[DashboardChartCard] Converting borderColor for ${mode}:`, {
                  original: originalColor,
                  converted: dataset.borderColor
                })
              }
            }
          }

          // Adjust pointBackgroundColor
          if (dataset.pointBackgroundColor) {
            dataset.pointBackgroundColor = convertColor(dataset.pointBackgroundColor, mode)
          }

          // Adjust pointBorderColor (usually white, but check)
          if (dataset.pointBorderColor && dataset.pointBorderColor !== '#fff' && dataset.pointBorderColor !== '#ffffff') {
            dataset.pointBorderColor = convertColor(dataset.pointBorderColor, mode)
          }
        })
      }

      return adjustedData
    })

    // Watch for colorblindness mode changes and force chart re-render
    watch(colorblindMode, () => {
      chartKey.value++
    })

    // Computed property for chart component
    const chartComponent = computed(() => {
      const componentMap = {
        'doughnut': 'Doughnut',
        'bar': 'Bar',
        'line': 'LineChart'
      }
      return componentMap[props.chartType] || 'Doughnut'
    })

    // Computed property to merge default chart options with provided options
    const mergedChartOptions = computed(() => {
      const providedOptions = { ...props.chartOptions }
      
      // For bar charts, add default options to reduce bar thickness
      if (props.chartType === 'bar') {
        // Default bar thickness settings - reduce bar size
        const mergedOptions = {
          ...providedOptions,
          // Set maxBarThickness to limit bar width (applies to all datasets)
          maxBarThickness: providedOptions.maxBarThickness ?? 40, // Limit maximum bar width to 40px
          elements: {
            ...providedOptions.elements,
            bar: {
              ...providedOptions.elements?.bar,
              // Reduce border width if not specified
              borderWidth: providedOptions.elements?.bar?.borderWidth ?? 1
            }
          },
          scales: {
            ...providedOptions.scales,
            x: {
              ...providedOptions.scales?.x,
              // Reduce bar thickness by decreasing categoryPercentage and barPercentage
              // These control how much of the category width is used for bars
              categoryPercentage: providedOptions.scales?.x?.categoryPercentage ?? 0.6, // Default is 0.8, reduced to 0.6
              barPercentage: providedOptions.scales?.x?.barPercentage ?? 0.6 // Default is 0.9, reduced to 0.6
            },
            y: {
              ...providedOptions.scales?.y
            }
          }
        }
        
        return mergedOptions
      }
      
      // For doughnut charts, add default cutout to ensure consistent thickness
      if (props.chartType === 'doughnut') {
        return {
          ...providedOptions,
          cutout: providedOptions.cutout ?? '70%' // Standardize doughnut chart thickness
        }
      }
      
      return providedOptions
    })

    return {
      colorblindMode,
      adjustedChartData,
      chartComponent,
      chartKey,
      mergedChartOptions
    }
  }
}
</script>

<style scoped>
@import './DashboardCards.css';
</style>

