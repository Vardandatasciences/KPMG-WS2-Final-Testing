<template>
  <div class="dropdown">
    <button 
      class="dropdown__button" 
      :class="{ 'dropdown__button--open': isOpen }" 
      @click="toggleDropdown"
      :disabled="disabled"
    >
      <PhCalendar v-if="showCalendarIcon" :size="16" />
      <span class="text-content">
        <span v-if="showLabel && config && (config.label || config.name)" class="dropdown-label">
          {{ config.label || config.name }}: 
        </span>
        <span class="dropdown-value">{{ selectedLabel }}</span>
      </span>
      <!-- Show clear button when value is selected and showClearButton is enabled, otherwise show dropdown arrow -->
      <button
        v-if="showClearButton && hasValue"
        class="dropdown__clear-button"
        @click.stop="clearSelection"
        type="button"
        title="Clear selection"
      >
        <i class="fas fa-times"></i>
      </button>
      <PhCaretDown v-else :size="16" />
    </button>
    <div v-if="isOpen" class="dropdown__menu">
      <div v-if="showSearchBar" class="dropdown__search">
        <input
          v-model="searchQuery"
          type="text"
          class="dropdown__search-input"
          placeholder="Search..."
          @click.stop
        />
      </div>
      <div 
        v-for="option in filteredOptions" 
        :key="option.value"
        class="dropdown__item"
        :class="{ 'dropdown__item--selected': showSelectedCheckmark && option.value === modelValue }"
        @click="selectOption(option)"
      >
        <span class="dropdown__item-text">{{ option.label }}</span>
        <span
          v-if="showSelectedCheckmark && option.value === modelValue"
          class="dropdown__item-check"
        >
          <svg class="dropdown__check-icon" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
          </svg>
        </span>
      </div>
      <div v-if="filteredOptions.length === 0" class="dropdown__no-results">
        No results found
      </div>
    </div>
  </div>
</template>

<script>
import { PhCalendar, PhCaretDown } from '@phosphor-icons/vue';

export default {
  name: 'CustomDropdown',
  components: {
    PhCalendar,
    PhCaretDown
  },
  props: {
    // Support both config object (old way) and options array (new way)
    config: {
      type: Object,
      required: false,
      default: null
    },
    options: {
      type: Array,
      required: false,
      default: null
    },
    modelValue: {
      type: [String, Number],
      default: ''
    },
    showSearchBar: {
      type: Boolean,
      default: true
    },
    placeholder: {
      type: String,
      default: 'Select an option'
    },
    disabled: {
      type: Boolean,
      default: false
    },
    showLabel: {
      type: Boolean,
      default: true
    },
    showSelectedCheckmark: {
      type: Boolean,
      default: false
    },
    showClearButton: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isOpen: false,
      searchQuery: ''
    }
  },
  computed: {
    // Normalize options from either config or options prop
    normalizedOptions() {
      if (this.options) {
        return this.options;
      }
      if (this.config) {
        return this.config.values || this.config.options || [];
      }
      return [];
    },
    selectedLabel() {
      const selectedOption = this.normalizedOptions.find(option => option.value === this.modelValue);
      if (selectedOption) {
        return selectedOption.label;
      }
      // No selection - use placeholder or config defaults
      if (this.config) {
        return this.config.defaultValue || this.config.defaultLabel || this.placeholder;
      }
      return this.placeholder;
    },
    showCalendarIcon() {
      if (!this.config) return false;
      return (this.config.label || this.config.name) === 'Due Date';
    },
    filteredOptions() {
      if (!this.searchQuery) return this.normalizedOptions;
      const query = this.searchQuery.toLowerCase();
      return this.normalizedOptions.filter(option =>
        option.label && option.label.toLowerCase().includes(query)
      );
    },
    hasValue() {
      // Check if modelValue is not empty and not null/undefined
      if (this.modelValue === '' || this.modelValue === null || this.modelValue === undefined) {
        return false;
      }
      // Check if the selected value matches a real option (not just placeholder)
      const selectedOption = this.normalizedOptions.find(option => {
        // Handle both string and number comparisons
        const optionValue = String(option.value || '');
        const modelValueStr = String(this.modelValue || '');
        return optionValue === modelValueStr && optionValue !== '';
      });
      return !!selectedOption;
    }
  },
  mounted() {
    // Add event listener for clicking outside
    document.addEventListener('click', this.closeDropdown);
  },
  // eslint-disable-next-line vue/no-deprecated-destroyed-lifecycle
  beforeDestroy() {
    // Remove event listener
    document.removeEventListener('click', this.closeDropdown);
  },
  methods: {
    toggleDropdown() {
      if (this.disabled) return;
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.searchQuery = '';
      }
    },
    selectOption(option) {
      if (this.disabled) return;
      this.$emit('update:modelValue', option.value);
      // Emit change event - for backward compatibility with old usage (config prop), emit full option
      // For new usage (options prop), components can access the value from modelValue
      this.$emit('change', this.config ? option : option.value);
      this.isOpen = false;
    },
    // Close dropdown when clicking outside
    closeDropdown(event) {
      if (!event.target.closest('.dropdown')) {
        this.isOpen = false;
      }
    },
    // Clear selection
    clearSelection() {
      if (this.disabled) return;
      this.$emit('update:modelValue', '');
      // Emit change event with empty value
      this.$emit('change', this.config ? { value: '' } : '');
    }
  }
}
</script>
