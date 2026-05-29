<template>
  <div class="dropdown">
    <!-- Draft persistence proxy: allows global form-draft logic to save/restore CustomDropdown -->
    <input
      v-if="shouldPersistDraft"
      type="text"
      class="dropdown__draft-proxy"
      :data-persist-key="draftPersistKey"
      :value="modelValue ?? ''"
      @input="handleDraftProxyInput"
      aria-label="dropdown-draft-proxy"
    />
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
        v-for="(option, idx) in filteredOptions" 
        :key="`dropdown-opt-${idx}-${String(option?.value ?? '')}`"
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
import { useFrameworkStore } from '@/stores/framework';

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
    },
    persistKey: {
      type: String,
      default: ''
    },
    persistDraft: {
      type: Boolean,
      default: true
    },
    /**
     * When false, do not narrow framework dropdown options to the session-selected framework.
     * Use on screens that must list all approved frameworks (e.g. Policy KPI) while v-model may be "all".
     */
    lockToSessionFramework: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      isOpen: false,
      searchQuery: '',
      lockedFrameworkId: '',
      lockedFrameworkName: ''
    }
  },
  computed: {
    // Normalize options from either config or options prop
    normalizedOptions() {
      let raw = []
      if (this.options) {
        raw = Array.isArray(this.options) ? this.options : []
      } else if (this.config) {
        raw = this.config.values || this.config.options || []
      }
      return raw.filter((o) => o && typeof o === 'object' && 'value' in o)
    },
    frameworkConstrainedOptions() {
      if (!this.isFrameworkSelector) return this.normalizedOptions;
      if (!this.lockToSessionFramework) return this.normalizedOptions;
      if (!this.lockedFrameworkId && !this.lockedFrameworkName) return this.normalizedOptions;

      const id = String(this.lockedFrameworkId || '').trim();
      const name = String(this.lockedFrameworkName || '').trim().toLowerCase();
      const constrained = this.normalizedOptions.filter(option => {
        const optionValue = String(option?.value ?? '').trim();
        const optionLabel = String(option?.label ?? '').trim().toLowerCase();
        if (id && optionValue === id) return true;
        if (name && (optionValue.toLowerCase() === name || optionLabel === name)) return true;
        return false;
      });

      if (constrained.length > 0) return constrained;

      // Hard lock: if a global framework is selected but current options are in a
      // different shape (ID vs name), do not fall back to showing all frameworks.
      if (this.lockedFrameworkName || this.lockedFrameworkId) {
        return [{
          value: this.modelValue || this.lockedFrameworkId || this.lockedFrameworkName,
          label: this.lockedFrameworkName || String(this.modelValue || this.lockedFrameworkId),
        }];
      }

      return this.normalizedOptions;
    },
    selectedLabel() {
      const selectedOption = this.frameworkConstrainedOptions.find(option => String(option.value) === String(this.modelValue));
      if (selectedOption) {
        return selectedOption.label;
      }
      if (this.isFrameworkSelector && this.lockedFrameworkName) {
        return this.lockedFrameworkName;
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
      if (!this.searchQuery) return this.frameworkConstrainedOptions;
      const query = this.searchQuery.toLowerCase();
      return this.frameworkConstrainedOptions.filter(option =>
        option.label && option.label.toLowerCase().includes(query)
      );
    },
    draftPersistKey() {
      if (!this.shouldPersistDraft) return '';
      if (this.persistKey) return this.persistKey;
      const baseName =
        this.config?.name ||
        this.config?.label ||
        this.placeholder ||
        'custom-dropdown';
      return `custom-dropdown:${baseName}`;
    },
    isFrameworkSelector() {
      const label = String(this.config?.label || this.config?.name || '').toLowerCase();
      const placeholder = String(this.placeholder || '').toLowerCase();
      const firstOptionLabel = String(this.normalizedOptions?.[0]?.label || '').toLowerCase();
      return (
        label.includes('framework') ||
        placeholder.includes('framework') ||
        firstOptionLabel.includes('framework')
      );
    },
    shouldPersistDraft() {
      // Prevent stale form-draft restore from overriding global framework selection.
      // Framework context is already handled centrally via Pinia/session.
      return this.persistDraft && !this.isFrameworkSelector;
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
    this.syncLockedFramework();
    window.addEventListener('framework-changed', this.syncLockedFramework);
  },
  // eslint-disable-next-line vue/no-deprecated-destroyed-lifecycle
  beforeDestroy() {
    // Remove event listener
    document.removeEventListener('click', this.closeDropdown);
    window.removeEventListener('framework-changed', this.syncLockedFramework);
  },
  methods: {
    syncLockedFramework() {
      try {
        const frameworkStore = useFrameworkStore();
        if (frameworkStore.selectedFrameworkId && frameworkStore.selectedFrameworkId !== 'all') {
          this.lockedFrameworkId = String(frameworkStore.selectedFrameworkId);
          this.lockedFrameworkName = frameworkStore.selectedFrameworkName || '';
        } else {
          this.lockedFrameworkId = '';
          this.lockedFrameworkName = '';
        }
      } catch (error) {
        this.lockedFrameworkId = '';
        this.lockedFrameworkName = '';
      }
    },
    toggleDropdown() {
      if (this.disabled) return;
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.searchQuery = '';
      }
    },
    selectOption(option) {
      if (this.disabled) return;
      if (!option || typeof option !== 'object' || !('value' in option)) {
        return;
      }
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
    },
    handleDraftProxyInput(event) {
      if (this.disabled) return;
      const value = event?.target?.value ?? '';
      this.$emit('update:modelValue', value);
      this.$emit('change', this.config ? { value } : value);
    }
  }
}
</script>

<style scoped>
.dropdown__draft-proxy {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
  border: 0;
  padding: 0;
  margin: 0;
}
</style>
