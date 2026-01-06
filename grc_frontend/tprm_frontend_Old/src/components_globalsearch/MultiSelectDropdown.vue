<template>
  <div class="relative" ref="dropdownRef">
    <!-- Dropdown Trigger -->
    <button
      @click="toggleDropdown"
      class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      :class="{ 'ring-2 ring-ring ring-offset-2': isOpen }"
    >
      <span class="flex items-center gap-1">
        {{ displayText }}
      </span>
      <ChevronDown 
        class="h-4 w-4 transition-transform duration-200" 
        :class="{ 'rotate-180': isOpen }"
      />
    </button>

    <!-- Dropdown Content -->
    <div
      v-if="isOpen"
      class="absolute top-full left-0 right-0 z-50 mt-1 max-h-60 overflow-auto rounded-md border bg-popover shadow-lg"
    >
      <div class="p-1">
        <!-- Select All Option -->
        <div 
          class="flex items-center space-x-2 rounded-sm px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground"
          @click="toggleSelectAll"
        >
          <input
            type="checkbox"
            :checked="allSelected"
            :indeterminate="someSelected && !allSelected"
            class="rounded border-gray-300 text-primary focus:ring-primary"
            @click.stop
          />
          <span class="font-medium">
            {{ allSelected ? 'Deselect All' : 'Select All' }}
          </span>
        </div>
        
        <div class="h-px bg-border my-1"></div>
        
        <!-- Individual Options -->
        <div 
          v-for="option in options" 
          :key="option.value"
          class="flex items-center space-x-2 rounded-sm px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground"
          @click="toggleOption(option.value)"
        >
          <input
            type="checkbox"
            :checked="modelValue.includes(option.value)"
            class="rounded border-gray-300 text-primary focus:ring-primary"
            @click.stop
          />
          <span>{{ option.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select options...'
  },
  selectedCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const dropdownRef = ref(null)

// Computed properties
const displayText = computed(() => {
  if (props.modelValue.length === 0) {
    return props.placeholder
  } else if (props.modelValue.length === 1) {
    const option = props.options.find(opt => opt.value === props.modelValue[0])
    return option ? option.label : 'Unknown'
  } else {
    return `${props.modelValue.length} selected`
  }
})

const allSelected = computed(() => {
  return props.options.length > 0 && props.modelValue.length === props.options.length
})

const someSelected = computed(() => {
  return props.modelValue.length > 0 && props.modelValue.length < props.options.length
})

// Methods
const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const toggleOption = (value) => {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(value)
  
  if (index > -1) {
    newValue.splice(index, 1)
  } else {
    newValue.push(value)
  }
  
  emit('update:modelValue', newValue)
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    emit('update:modelValue', [])
  } else {
    emit('update:modelValue', props.options.map(option => option.value))
  }
}

// Click outside handler
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Custom checkbox styling */
input[type="checkbox"] {
  accent-color: rgb(var(--primary));
}

/* Indeterminate checkbox styling */
input[type="checkbox"]:indeterminate {
  background-color: rgb(var(--primary));
  border-color: rgb(var(--primary));
}
</style>
