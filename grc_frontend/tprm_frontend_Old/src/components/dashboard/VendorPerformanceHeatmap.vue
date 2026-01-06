<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <BarChart3 class="h-5 w-5" />
        Vendor Performance Heatmap
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div class="space-y-4">
        <div class="grid grid-cols-5 gap-2">
          <div class="text-xs text-muted-foreground text-center">Vendor</div>
          <div class="text-xs text-muted-foreground text-center">Uptime</div>
          <div class="text-xs text-muted-foreground text-center">Response</div>
          <div class="text-xs text-muted-foreground text-center">Support</div>
          <div class="text-xs text-muted-foreground text-center">Overall</div>
        </div>
        <div v-for="vendor in vendors" :key="vendor.name" class="grid grid-cols-5 gap-2">
          <div class="text-sm font-medium">{{ vendor.name }}</div>
          <div 
            :class="[
              'h-6 rounded text-xs flex items-center justify-center text-white',
              getPerformanceColor(vendor.uptime)
            ]"
          >
            {{ vendor.uptime }}%
          </div>
          <div 
            :class="[
              'h-6 rounded text-xs flex items-center justify-center text-white',
              getPerformanceColor(vendor.response)
            ]"
          >
            {{ vendor.response }}%
          </div>
          <div 
            :class="[
              'h-6 rounded text-xs flex items-center justify-center text-white',
              getPerformanceColor(vendor.support)
            ]"
          >
            {{ vendor.support }}%
          </div>
          <div 
            :class="[
              'h-6 rounded text-xs flex items-center justify-center text-white',
              getPerformanceColor(vendor.overall)
            ]"
          >
            {{ vendor.overall }}%
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
import { ref } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart3 } from 'lucide-vue-next'

const vendors = ref([
  { name: 'AWS', uptime: 99.9, response: 95, support: 88, overall: 94 },
  { name: 'Oracle', uptime: 99.8, response: 92, support: 85, overall: 92 },
  { name: 'Microsoft', uptime: 99.7, response: 89, support: 82, overall: 90 },
  { name: 'Salesforce', uptime: 99.5, response: 87, support: 80, overall: 89 },
  { name: 'IBM', uptime: 99.3, response: 85, support: 78, overall: 87 }
])

const getPerformanceColor = (score) => {
  if (score >= 95) return 'bg-green-600'
  if (score >= 90) return 'bg-green-500'
  if (score >= 85) return 'bg-yellow-500'
  if (score >= 80) return 'bg-orange-500'
  return 'bg-red-500'
}
</script>
