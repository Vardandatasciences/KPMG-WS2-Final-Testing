<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <TrendingUp class="h-5 w-5" />
        Performance Trends
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div class="h-64">
        <!-- Simple CSS-based chart -->
        <div class="flex items-end justify-between h-full gap-2 p-4">
          <div v-for="(item, index) in trendData" :key="item.month" class="flex flex-col items-center flex-1">
            <div class="flex flex-col items-center gap-1 mb-2">
              <div 
                class="w-8 bg-green-500 rounded-t"
                :style="{ height: `${(item.compliance / 100) * 120}px` }"
                :title="`Compliance: ${item.compliance}%`"
              ></div>
              <div 
                class="w-8 bg-red-500 rounded-t"
                :style="{ height: `${(item.violations / 10) * 120}px` }"
                :title="`Violations: ${item.violations}%`"
              ></div>
            </div>
            <span class="text-xs text-muted-foreground">{{ item.month }}</span>
          </div>
        </div>
        
        <!-- Legend -->
        <div class="flex justify-center gap-4 mt-4 text-sm">
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 bg-green-500 rounded"></div>
            <span>Compliance Rate</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 bg-red-500 rounded"></div>
            <span>Violation Rate</span>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
import { ref } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp } from 'lucide-vue-next'

const trendData = ref([
  { month: 'Jan', compliance: 92.1, violations: 7.9 },
  { month: 'Feb', compliance: 93.5, violations: 6.5 },
  { month: 'Mar', compliance: 91.8, violations: 8.2 },
  { month: 'Apr', compliance: 94.2, violations: 5.8 },
  { month: 'May', compliance: 95.1, violations: 4.9 },
  { month: 'Jun', compliance: 94.7, violations: 5.3 }
])
</script>
