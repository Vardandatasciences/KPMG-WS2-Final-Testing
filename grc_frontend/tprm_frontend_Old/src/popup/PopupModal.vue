<template>
  <div v-if="visible" class="popup-backdrop" @keydown.esc="onClose" tabindex="0" aria-modal="true" role="dialog">
    <div class="popup-modal" :class="type">
      <div class="popup-icon" v-if="icon">
        <span v-html="icon"></span>
      </div>
      <h2 class="popup-heading">{{ heading }}</h2>
      <p class="popup-message">{{ message }}</p>
      <textarea
        v-if="type === 'comment'"
        v-model="comment"
        class="popup-input"
        :placeholder="inputPlaceholder"
        @keydown.enter.stop
      ></textarea>
      <select
        v-if="type === 'select'"
        v-model="selectedValue"
        class="popup-select"
      >
        <option v-for="option in selectOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <div class="popup-actions">
        <button
          v-for="(btn, idx) in buttons"
          :key="idx"
          @click="onAction(btn.action)"
          :class="btn.class"
          
        >{{ btn.label }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { PopupService } from './popupService';

const ICONS = {
  success: '✓',
  error: '✗',
  warning: '⚠️',
  info: 'ℹ️',
  confirm: '❓',
  comment: '💬',
  select: '📋',
  'access-denied': '🚫'
};

export default {
  name: 'PopupModal',
  setup() {
    const popupState = PopupService.getState();

    return {
      popupState
    };
  },
  computed: {
    visible() {
      return this.popupState.visible;
    },
    type() {
      return this.popupState.type;
    },
    heading() {
      return this.popupState.heading;
    },
    message() {
      return this.popupState.message;
    },
    buttons() {
      return this.popupState.buttons;
    },
    autoClose() {
      return this.popupState.autoClose;
    },
    icon() {
      return ICONS[this.type] || '';
    },
    selectOptions() {
      return this.popupState.selectOptions || [];
    },
    inputPlaceholder() {
      return this.popupState.inputPlaceholder;
    }
  },
  watch: {
    visible(val) {
      if (val && this.autoClose > 0) {
        setTimeout(() => this.onAction('auto-close'), this.autoClose);
      }
      if (val) {
        this.comment = '';
        this.selectedValue = this.popupState.selectedValue || '';
      }
    }
  },
  data() {
    return { comment: '', selectedValue: '' }
  },
  methods: {
    onClose() {
      this.onAction('close');
    },
    onAction(action) {
      if (this.type === 'comment') {
        PopupService.handleAction({ action, comment: this.comment });
      } else if (this.type === 'select') {
        PopupService.handleAction({ action, comment: this.selectedValue });
      } else {
        PopupService.handleAction({ action });
      }
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* Use TPRM design system colors */
.popup-backdrop {
  position: fixed !important;
  top: 0 !important; 
  left: 0 !important; 
  width: 100vw !important; 
  height: 100vh !important;
  background: rgba(0, 0, 0, 0.5) !important;
  display: flex !important; 
  align-items: center !important; 
  justify-content: center !important; 
  z-index: 10000 !important;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  backdrop-filter: none !important;
}

.popup-backdrop[class*="modal-overlay"],
.popup-backdrop[class*="modal"] {
  background: rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: none !important;
}

.popup-modal {
  background: hsl(0, 0%, 100%) !important;
  border-radius: 0.5rem;
  padding: 1.5rem;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  text-align: center;
  position: relative;
  border: 1px solid hsl(210, 20%, 90%);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.popup-modal[class*="modal"],
.popup-modal[class*="overlay"] {
  background: hsl(0, 0%, 100%) !important;
  backdrop-filter: none !important;
}

/* Colored left border accent for each type */
.success.popup-modal { border-left: 4px solid hsl(142, 76%, 36%); }
.error.popup-modal { border-left: 4px solid hsl(0, 84%, 60%); }
.warning.popup-modal { border-left: 4px solid hsl(38, 92%, 50%); }
.info.popup-modal { border-left: 4px solid hsl(217, 91%, 60%); }
.confirm.popup-modal { border-left: 4px solid hsl(217, 91%, 60%); }
.comment.popup-modal { border-left: 4px solid hsl(217, 91%, 60%); }
.select.popup-modal { border-left: 4px solid hsl(217, 91%, 60%); }
.access-denied.popup-modal { border-left: 4px solid hsl(0, 84%, 60%); }

.popup-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background: hsl(210, 17%, 95%);
  color: hsl(217, 91%, 60%);
}

.success .popup-icon { background: hsl(142, 76%, 95%); color: hsl(142, 76%, 36%); }
.error .popup-icon { background: hsl(0, 84%, 95%); color: hsl(0, 84%, 60%); }
.warning .popup-icon { background: hsl(38, 92%, 95%); color: hsl(38, 92%, 50%); }
.info .popup-icon { background: hsl(217, 91%, 95%); color: hsl(217, 91%, 60%); }
.confirm .popup-icon { background: hsl(217, 91%, 95%); color: hsl(217, 91%, 60%); }
.comment .popup-icon { background: hsl(217, 91%, 95%); color: hsl(217, 91%, 60%); }
.select .popup-icon { background: hsl(217, 91%, 95%); color: hsl(217, 91%, 60%); }
.access-denied .popup-icon { background: hsl(0, 84%, 95%); color: hsl(0, 84%, 60%); }

.popup-heading {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.75rem;
  color: hsl(215, 25%, 27%);
  letter-spacing: -0.025em;
}

.popup-message {
  margin-bottom: 1.5rem;
  color: hsl(215, 13%, 65%);
  font-size: 0.875rem;
  line-height: 1.5;
}

.popup-input {
  width: 100%;
  min-height: 3.5rem;
  margin-bottom: 1rem;
  border-radius: calc(0.5rem - 2px);
  border: 1px solid hsl(210, 20%, 90%);
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  background: hsl(0, 0%, 100%);
  color: hsl(215, 25%, 27%);
  resize: vertical;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
}

.popup-input:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
  border-color: hsl(217, 91%, 60%);
}

.popup-input::placeholder {
  color: hsl(215, 13%, 65%);
}

.popup-select {
  width: 100%;
  height: 2.5rem;
  margin-bottom: 1rem;
  border-radius: calc(0.5rem - 2px);
  border: 1px solid hsl(210, 20%, 90%);
  padding: 0 0.75rem;
  font-size: 0.875rem;
  background: hsl(0, 0%, 100%);
  color: hsl(215, 25%, 27%);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  font-family: inherit;
}

.popup-select:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
  border-color: hsl(217, 91%, 60%);
}

.popup-actions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  padding: 0.5rem 1rem;
  height: 2.5rem;
  border-radius: calc(0.5rem - 2px);
  border: 1px solid transparent;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  background-color: hsl(217, 91%, 60%);
  color: hsl(0, 0%, 100%);
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  outline: 2px solid transparent;
  outline-offset: 2px;
}

button:hover {
  background-color: hsl(217, 91%, 55%);
}

button.success {
  background-color: hsl(142, 76%, 36%);
}

button.success:hover {
  background-color: hsl(142, 76%, 32%);
}

button.error {
  background-color: hsl(0, 84%, 60%);
}

button.error:hover {
  background-color: hsl(0, 84%, 55%);
}

button.warning {
  background-color: hsl(38, 92%, 50%);
  color: hsl(0, 0%, 100%);
}

button.warning:hover {
  background-color: hsl(38, 92%, 45%);
}

button:active {
  transform: scale(0.98);
}

button:focus-visible {
  outline: 2px solid hsl(217, 91%, 60%);
  outline-offset: 2px;
}

button:disabled {
  pointer-events: none;
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 500px) {
  .popup-modal {
    padding: 1.25rem;
    width: 90vw;
  }
  
  .popup-heading {
    font-size: 1.125rem;
  }
  
  .popup-icon {
    font-size: 1.5rem;
    width: 2.5rem;
    height: 2.5rem;
  }
  
  .popup-actions {
    flex-direction: column;
    width: 100%;
  }
  
  button {
    width: 100%;
  }
}
</style> 