<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold">Vendor Performance Summary</h1>
      <p class="text-muted-foreground">Overview of vendor-wise SLA performance</p>
    </div>

    <Card>
      <CardContent class="p-6">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-left text-muted-foreground">
              <tr>
                <th class="py-2 pr-4">Vendor</th>
                <th class="py-2 pr-4">Compliance</th>
                <th class="py-2 pr-4">Response Time</th>
                <th class="py-2 pr-4">Uptime</th>
                <th class="py-2 pr-4">Status</th>
                <th class="py-2">SLAs</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in vendors" :key="v.name" class="border-t">
                <td class="py-2 pr-4 font-medium">{{ v.name }}</td>
                <td class="py-2 pr-4">{{ v.compliance }}%</td>
                <td class="py-2 pr-4">{{ v.responseTime }}s</td>
                <td class="py-2 pr-4">{{ v.uptime }}%</td>
                <td class="py-2 pr-4 capitalize">{{ v.status }}</td>
                <td class="py-2">{{ v.slaCount }}</td>
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
import { Card, CardContent } from '@/components/ui/card'
import perf from '@/data/performance-data.json'

const vendors = ref(perf.performanceDashboard.vendorPerformance)
</script>

