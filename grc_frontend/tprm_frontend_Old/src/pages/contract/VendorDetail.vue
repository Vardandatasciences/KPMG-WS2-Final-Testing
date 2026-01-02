<template>
  <div class="space-y-6">
    <!-- Vendor Not Found -->
    <div v-if="!vendor" class="text-center">
      <h1 class="text-2xl font-bold text-foreground">Vendor Not Found</h1>
      <p class="text-muted-foreground mt-2">The requested vendor could not be found.</p>
      <Button @click="navigate('/vendors')" class="mt-4">
        Back to Vendors
      </Button>
    </div>

    <!-- Vendor Details -->
    <div v-else class="space-y-6">
      <div class="flex items-center gap-4">
        <Button variant="ghost" @click="navigate('/vendors')">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Vendors
        </Button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">{{ vendor.name }}</h1>
          <p class="text-muted-foreground">Vendor Details & Contracts</p>
        </div>
      </div>

      <!-- Vendor Information -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-3">
            <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Building2 class="w-6 h-6 text-primary" />
            </div>
            <div>
              <div class="text-xl font-bold">{{ vendor.name }}</div>
              <div class="text-sm text-muted-foreground">{{ vendor.id }}</div>
            </div>
            <Badge :variant="vendor.status === 'Active' ? 'default' : 'secondary'">
              {{ vendor.status }}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="space-y-3">
              <h3 class="font-medium text-foreground">Contact Information</h3>
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-sm">
                  <Mail class="w-4 h-4 text-muted-foreground" />
                  {{ vendor.email }}
                </div>
                <div class="flex items-center gap-2 text-sm">
                  <Phone class="w-4 h-4 text-muted-foreground" />
                  {{ vendor.phone }}
                </div>
                <div class="flex items-center gap-2 text-sm">
                  <MapPin class="w-4 h-4 text-muted-foreground" />
                  {{ vendor.address }}
                </div>
              </div>
            </div>
            
            <div>
              <h3 class="font-medium text-foreground mb-2">Total Contracts</h3>
              <div class="text-2xl font-bold text-primary">{{ vendor.contractsCount }}</div>
            </div>
            
            <div>
              <h3 class="font-medium text-foreground mb-2">Total Value</h3>
              <div class="text-2xl font-bold text-primary">${{ vendor.totalValue.toLocaleString() }}</div>
            </div>
            
            <div>
              <h3 class="font-medium text-foreground mb-2">Last Activity</h3>
              <div class="text-lg text-muted-foreground">{{ vendor.lastActivity }}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Contracts List -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <FileText class="w-5 h-5" />
            Contracts
          </CardTitle>
          <CardDescription>All contracts associated with this vendor</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contract Details</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Start Date</TableHead>
                <TableHead>End Date</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="contract in vendor.contracts" :key="contract.id">
                <TableCell>
                  <div>
                    <div class="font-medium text-foreground">{{ contract.title }}</div>
                    <div class="text-sm text-muted-foreground">{{ contract.id }}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{{ contract.type }}</Badge>
                </TableCell>
                <TableCell>
                  <Badge :variant="contract.status === 'Active' ? 'default' : 'secondary'">
                    {{ contract.status }}
                  </Badge>
                </TableCell>
                <TableCell>{{ contract.startDate }}</TableCell>
                <TableCell>{{ contract.endDate }}</TableCell>
                <TableCell class="font-medium">${{ contract.value.toLocaleString() }}</TableCell>
                <TableCell>
                  <Button 
                    variant="outline" 
                    size="sm"
                    @click="navigate(`/contracts/${contract.id}`)"
                  >
                    View Contract
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import loggingService from '@/services/loggingService'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui_contract'
import { 
  ArrowLeft, Building2, Mail, Phone, MapPin, FileText 
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

// Mock data for vendor and their contracts
const getVendorData = (id) => {
  const vendors = {
    "VEN001": {
      id: "VEN001",
      name: "TechCorp Solutions",
      email: "contact@techcorp.com",
      phone: "+1 (555) 123-4567",
      address: "123 Tech Street, Silicon Valley, CA",
      status: "Active",
      contractsCount: 8,
      totalValue: 250000,
      lastActivity: "2024-01-15",
      contracts: [
        {
          id: "CON001",
          title: "Software Development Agreement",
          status: "Active",
          startDate: "2024-01-01",
          endDate: "2024-12-31",
          value: 50000,
          type: "Development"
        },
        {
          id: "CON002",
          title: "Maintenance Support Contract",
          status: "Active",
          startDate: "2024-02-01",
          endDate: "2025-01-31",
          value: 25000,
          type: "Support"
        },
        {
          id: "CON003",
          title: "Cloud Infrastructure Services",
          status: "Pending",
          startDate: "2024-03-01",
          endDate: "2024-08-31",
          value: 75000,
          type: "Infrastructure"
        }
      ]
    },
    "VEN002": {
      id: "VEN002",
      name: "Global Services Ltd",
      email: "info@globalservices.com",
      phone: "+1 (555) 987-6543",
      address: "456 Business Ave, New York, NY",
      status: "Active",
      contractsCount: 12,
      totalValue: 450000,
      lastActivity: "2024-01-10",
      contracts: [
        {
          id: "CON004",
          title: "Marketing Campaign Management",
          status: "Active",
          startDate: "2023-12-01",
          endDate: "2024-11-30",
          value: 150000,
          type: "Marketing"
        },
        {
          id: "CON005",
          title: "Digital Transformation Consulting",
          status: "Active",
          startDate: "2024-01-15",
          endDate: "2024-06-15",
          value: 100000,
          type: "Consulting"
        }
      ]
    },
    "VEN003": {
      id: "VEN003",
      name: "Innovation Partners",
      email: "hello@innovation.com", 
      phone: "+1 (555) 456-7890",
      address: "789 Innovation Blvd, Austin, TX",
      status: "Inactive",
      contractsCount: 3,
      totalValue: 75000,
      lastActivity: "2023-12-20",
      contracts: [
        {
          id: "CON006",
          title: "Research & Development Partnership",
          status: "Completed",
          startDate: "2023-06-01",
          endDate: "2023-12-01",
          value: 30000,
          type: "Research"
        }
      ]
    },
    "VEN004": {
      id: "VEN004",
      name: "TechGuard Solutions",
      email: "info@techguard.com",
      phone: "+1 (555) 321-6540",
      address: "321 Security Way, San Francisco, CA",
      status: "Active",
      contractsCount: 5,
      totalValue: 180000,
      lastActivity: "2024-01-20",
      contracts: [
        {
          id: "CON007",
          title: "Cybersecurity Services",
          status: "Active",
          startDate: "2024-01-01",
          endDate: "2024-12-31",
          value: 120000,
          type: "Security"
        },
        {
          id: "CON008",
          title: "Network Monitoring",
          status: "Active",
          startDate: "2024-02-01",
          endDate: "2025-01-31",
          value: 60000,
          type: "Monitoring"
        }
      ]
    },
    "VEN005": {
      id: "VEN005",
      name: "Expert Advisors LLC",
      email: "contact@expertadvisors.com",
      phone: "+1 (555) 789-0123",
      address: "654 Consulting Blvd, Chicago, IL",
      status: "Active",
      contractsCount: 7,
      totalValue: 220000,
      lastActivity: "2024-01-18",
      contracts: [
        {
          id: "CON009",
          title: "Strategic Planning Services",
          status: "Active",
          startDate: "2024-01-01",
          endDate: "2024-06-30",
          value: 80000,
          type: "Consulting"
        },
        {
          id: "CON010",
          title: "Business Process Optimization",
          status: "Active",
          startDate: "2024-02-01",
          endDate: "2024-11-30",
          value: 140000,
          type: "Optimization"
        }
      ]
    }
  }
  
  return vendors[id] || null
}

// Get vendor data based on route parameter
const vendor = computed(() => getVendorData(route.params.id))

// Navigation method
const navigate = (path) => router.push(path)

// Log page view on mount
onMounted(async () => {
  const vendorId = route.params.id
  await loggingService.logPageView('Contract', 'Vendor Detail', vendorId)
})
</script>
