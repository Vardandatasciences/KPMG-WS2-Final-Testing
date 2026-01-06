<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold">Trend Analysis</h1>
      <p class="text-muted-foreground">Analyze performance trends and patterns</p>
    </div>

    <!-- Trend Summary -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted-foreground">Overall Trend</p>
              <p class="text-2xl font-bold" :class="trendStats.overall > 0 ? 'text-green-600' : 'text-red-600'">
                {{ trendStats.overall > 0 ? '+' : '' }}{{ trendStats.overall }}%
              </p>
            </div>
            <TrendingUp v-if="trendStats.overall > 0" class="h-8 w-8 text-green-500" />
            <TrendingDown v-else class="h-8 w-8 text-red-500" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted-foreground">Performance</p>
              <p class="text-2xl font-bold" :class="trendStats.performance > 0 ? 'text-green-600' : 'text-red-600'">
                {{ trendStats.performance > 0 ? '+' : '' }}{{ trendStats.performance }}%
              </p>
            </div>
            <Activity class="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted-foreground">Compliance</p>
              <p class="text-2xl font-bold" :class="trendStats.compliance > 0 ? 'text-green-600' : 'text-red-600'">
                {{ trendStats.compliance > 0 ? '+' : '' }}{{ trendStats.compliance }}%
              </p>
            </div>
            <Shield class="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-muted-foreground">Risk Level</p>
              <p class="text-2xl font-bold" :class="getRiskClass(trendStats.riskLevel)">
                {{ trendStats.riskLevel }}
              </p>
            </div>
            <AlertTriangle class="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Trend Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="h-64 flex items-center justify-center bg-muted/20 rounded-lg">
            <div class="text-center">
              <BarChart3 class="h-12 w-12 text-muted-foreground mx-auto mb-2" />
              <p class="text-sm text-muted-foreground">Performance trend chart</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Compliance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="h-64 flex items-center justify-center bg-muted/20 rounded-lg">
            <div class="text-center">
              <LineChart class="h-12 w-12 text-muted-foreground mx-auto mb-2" />
              <p class="text-sm text-muted-foreground">Compliance trend chart</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Trend Analysis Table -->
    <Card>
      <CardHeader>
        <CardTitle>Detailed Trend Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-left text-muted-foreground">
              <tr>
                <th class="py-2 pr-4">Metric</th>
                <th class="py-2 pr-4">Current</th>
                <th class="py-2 pr-4">Previous</th>
                <th class="py-2 pr-4">Change</th>
                <th class="py-2 pr-4">Trend</th>
                <th class="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="trend in trendData" :key="trend.metric" class="border-t">
                <td class="py-2 pr-4 font-medium">{{ trend.metric }}</td>
                <td class="py-2 pr-4">{{ trend.current }}</td>
                <td class="py-2 pr-4">{{ trend.previous }}</td>
                <td class="py-2 pr-4" :class="trend.change > 0 ? 'text-green-600' : 'text-red-600'">
                  {{ trend.change > 0 ? '+' : '' }}{{ trend.change }}%
                </td>
                <td class="py-2 pr-4">
                  <div class="flex items-center gap-1">
                    <TrendingUp v-if="trend.change > 0" class="h-4 w-4 text-green-500" />
                    <TrendingDown v-else class="h-4 w-4 text-red-500" />
                    <span class="text-xs">{{ trend.trend }}</span>
                  </div>
                </td>
                <td class="py-2">
                  <Badge :class="getStatusClass(trend.status)">
                    {{ trend.status }}
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Activity, Shield, AlertTriangle, BarChart3, LineChart } from 'lucide-vue-next'

const trendStats = ref({
  overall: 5.2,
  performance: 3.8,
  compliance: 7.1,
  riskLevel: "Low"
})

const trendData = ref([
  {
    metric: "Response Time",
    current: "0.8s",
    previous: "0.9s",
    change: 11.1,
    trend: "Improving",
    status: "good"
  },
  {
    metric: "Uptime",
    current: "99.95%",
    previous: "99.92%",
    change: 0.03,
    trend: "Stable",
    status: "good"
  },
  {
    metric: "Error Rate",
    current: "0.05%",
    previous: "0.08%",
    change: -37.5,
    trend: "Improving",
    status: "good"
  }
])

const getRiskClass = (risk: string) => {
  switch (risk.toLowerCase()) {
    case 'low':
      return 'text-green-600'
    case 'medium':
      return 'text-yellow-600'
    case 'high':
      return 'text-orange-600'
    case 'critical':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'good':
      return 'bg-green-100 text-green-800'
    case 'warning':
      return 'bg-yellow-100 text-yellow-800'
    case 'critical':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}
</script>
