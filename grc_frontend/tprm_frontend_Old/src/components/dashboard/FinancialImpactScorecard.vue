<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <DollarSign class="h-5 w-5" />
        Financial Impact
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <span class="text-sm text-muted-foreground">Penalties Applied</span>
          <span class="font-semibold text-red-600">-$45,200</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-sm text-muted-foreground">Credits Earned</span>
          <span class="font-semibold text-green-600">+$12,800</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-sm text-muted-foreground">Net Impact</span>
          <span class="font-semibold text-orange-600">-$32,400</span>
        </div>
        <div class="pt-2 border-t">
          <div class="text-xs text-muted-foreground mb-1">This Month</div>
          <div class="w-full bg-gray-200 rounded-full h-1">
            <div class="bg-orange-500 h-1 rounded-full" style="width: 65%"></div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DollarSign } from 'lucide-vue-next'
</script>
