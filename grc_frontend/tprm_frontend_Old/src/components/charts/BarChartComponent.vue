<template>
  <div class="chart-container">
    <canvas ref="chartRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  layout: {
    type: String,
    default: 'vertical'
  },
  height: {
    type: Number,
    default: 300
  },
  dataKey: {
    type: String,
    default: 'count'
  },
  colors: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref()
let chart = null

const createChart = () => {
  if (!chartRef.value) return

  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return

  const isHorizontal = props.layout === 'horizontal'
  const labels = props.data.map(item => item.name)
  const values = props.data.map(item => item[props.dataKey])

  const chartData = {
    labels,
    datasets: [{
      label: props.dataKey === 'count' ? 'Count' : 'Value',
      data: values,
      backgroundColor: props.colors.length > 0 ? props.colors : 'hsl(var(--primary))',
      borderColor: props.colors.length > 0 ? props.colors : 'hsl(var(--primary))',
      borderWidth: 1,
      borderRadius: 4
    }]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: isHorizontal ? 'y' : 'x',
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            if (props.dataKey === 'value') {
              return `$${context.parsed.y || context.parsed.x}K`
            }
            return `${context.parsed.y || context.parsed.x}`
          }
        }
      }
    },
    scales: {
      x: {
        type: isHorizontal ? 'linear' : 'category',
        grid: {
          display: true,
          drawBorder: false,
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      y: {
        type: isHorizontal ? 'category' : 'linear',
        grid: {
          display: true,
          drawBorder: false,
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    }
  }

  chart = new Chart(ctx, {
    type: 'bar',
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
