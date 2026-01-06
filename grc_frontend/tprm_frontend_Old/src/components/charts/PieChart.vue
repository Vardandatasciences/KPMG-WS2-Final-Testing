<template>
  <div class="chart-container">
    <canvas ref="chartRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Chart, DoughnutController, ArcElement, Tooltip, Legend } from 'chart.js'

Chart.register(DoughnutController, ArcElement, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  colors: {
    type: Object,
    default: () => ({
      'Active': '#22c55e',
      'Draft': '#94a3b8',
      'Review': '#f59e0b',
      'Expired': '#ef4444',
      'Terminated': '#ef4444',
      'Low': '#22c55e',
      'Medium': '#f59e0b',
      'High': '#ef4444'
    })
  },
  height: {
    type: Number,
    default: 300
  }
})

const chartRef = ref()
let chart = null

const createChart = () => {
  if (!chartRef.value) return

  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return

  const chartData = {
    labels: props.data.map(item => item.name),
    datasets: [{
      data: props.data.map(item => item.value),
      backgroundColor: props.data.map(item => props.colors[item.name] || '#94a3b8'),
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          usePointStyle: true,
          padding: 20
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const total = props.data.reduce((sum, item) => sum + item.value, 0)
            const percentage = ((context.parsed / total) * 100).toFixed(1)
            return `${context.label}: ${context.parsed} (${percentage}%)`
          }
        }
      }
    }
  }

  chart = new Chart(ctx, {
    type: 'doughnut',
    data: chartData,
    options
  })
}

const destroyChart = () => {
  if (chart) {
    chart.destroy()
    chart = null
  }
}

onMounted(() => {
  createChart()
})

onUnmounted(() => {
  destroyChart()
})

watch(() => props.data, () => {
  destroyChart()
  createChart()
}, { deep: true })
</script>

<style scoped>
.chart-container {
  height: v-bind(height + 'px');
  width: 100%;
}
</style>
