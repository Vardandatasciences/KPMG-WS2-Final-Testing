import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useVendorVendorsStore = defineStore('vendor_vendors', () => {
  // State
  const vendor_currentVendor = ref({
    vendorCode: 'VEND001',
    companyName: 'Acme Corporation',
    legalName: 'Acme Corporation Inc.',
    businessType: '',
    taxId: '12-3456789',
    dunsNumber: '123456789',
    incorporationDate: '',
    industrySector: '',
    website: 'https://acme.com',
    annualRevenue: '$10,000,000',
    employeeCount: '500',
    headquarters: '',
    vendorCategory: '',
    riskLevel: '',
    status: '',
    isCritical: false,
    hasDataAccess: false,
    hasSystemAccess: false,
    description: ''
  })

  const vendor_contacts = ref([
    {
      id: "1",
      name: "John Smith",
      email: "john@acme.com",
      phone: "+1-555-0123",
      role: "Primary",
      isPrimary: true
    },
    {
      id: "2",
      name: "Sarah Johnson",
      email: "sarah@acme.com",
      phone: "+1-555-0124",
      role: "Finance",
      isPrimary: false
    }
  ])

  const vendor_documents = ref([
    {
      id: "1",
      name: "Business_License.pdf",
      type: "License",
      version: "1.0",
      status: "Approved",
      expiryDate: "2026-01-01"
    },
    {
      id: "2",
      name: "GST_Certificate.pdf",
      type: "Certificate",
      version: "1.2",
      status: "Pending",
      expiryDate: "2025-12-31"
    }
  ])

  // Getters
  const vendor_getCurrentVendor = computed(() => vendor_currentVendor.value)
  const vendor_getContacts = computed(() => vendor_contacts.value)
  const vendor_getDocuments = computed(() => vendor_documents.value)
  const vendor_getPrimaryContact = computed(() => vendor_contacts.value.find(c => c.isPrimary))

  // Actions
  const vendor_updateVendorField = (field, value) => {
    vendor_currentVendor.value[field] = value
  }

  const vendor_addContact = (contact) => {
    vendor_contacts.value.push(contact)
  }

  const vendor_removeContact = (id) => {
    vendor_contacts.value = vendor_contacts.value.filter(c => c.id !== id)
  }

  const vendor_updateContact = (id, updates) => {
    const index = vendor_contacts.value.findIndex(c => c.id === id)
    if (index !== -1) {
      vendor_contacts.value[index] = { ...vendor_contacts.value[index], ...updates }
    }
  }

  const vendor_addDocument = (document) => {
    vendor_documents.value.push(document)
  }

  const vendor_removeDocument = (id) => {
    vendor_documents.value = vendor_documents.value.filter(d => d.id !== id)
  }

  const vendor_updateDocumentStatus = (id, status) => {
    const document = vendor_documents.value.find(d => d.id === id)
    if (document) {
      document.status = status
    }
  }

  return {
    vendor_currentVendor,
    vendor_contacts,
    vendor_documents,
    vendor_getCurrentVendor,
    vendor_getContacts,
    vendor_getDocuments,
    vendor_getPrimaryContact,
    vendor_updateVendorField,
    vendor_addContact,
    vendor_removeContact,
    vendor_updateContact,
    vendor_addDocument,
    vendor_removeDocument,
    vendor_updateDocumentStatus
  }
})
