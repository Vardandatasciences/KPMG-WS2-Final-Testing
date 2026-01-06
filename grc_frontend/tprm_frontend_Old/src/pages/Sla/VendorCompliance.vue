<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold">Vendor Compliance</h1>
      <p class="text-muted-foreground">Monitor vendor compliance status</p>
    </div>

    <Card>
      <CardContent class="p-6">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-left text-muted-foreground">
              <tr>
                <th class="py-2 pr-4">Framework</th>
                <th class="py-2 pr-4">Vendor</th>
                <th class="py-2 pr-4">SLA</th>
                <th class="py-2 pr-4">Score</th>
                <th class="py-2 pr-4">Status</th>
                <th class="py-2">Next Audit</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in frameworks" :key="f.id" class="border-t">
                <td class="py-2 pr-4 font-medium">{{ f.name }}</td>
                <td class="py-2 pr-4">{{ f.vendor }}</td>
                <td class="py-2 pr-4">{{ f.slaName }}</td>
                <td class="py-2 pr-4">{{ f.complianceScore }}%</td>
                <td class="py-2 pr-4 capitalize">{{ f.status }}</td>
                <td class="py-2">{{ f.nextAuditDate }}</td>
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
import comp from '@/data/compliance-data.json'

const frameworks = ref(comp.complianceFrameworks)
</script>
