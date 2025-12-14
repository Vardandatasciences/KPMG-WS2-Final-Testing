<template>
  <div class="CC_container">
    <div class="CC_header">
      <button @click="goBack" class="CC_back-button">
        <i class="fas fa-arrow-left"></i>
        Back
      </button>
      <h2>Checklisted Compliances</h2>
      <div class="CC_header-actions">
        <button @click="selectAll" class="CC_action-button">
          <i class="fas fa-check-square"></i>
          Select All
        </button>
        <button @click="deselectAll" class="CC_action-button">
          <i class="fas fa-square"></i>
          Deselect All
        </button>
        <button 
          @click="saveSelectedCompliances" 
          class="CC_save-button"
          :disabled="selectedCompliances.length === 0 || saving"
        >
          <i v-if="!saving" class="fas fa-save"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ saving ? 'Saving...' : `Save Selected (${selectedCompliances.length})` }}
        </button>
      </div>
    </div>

    <div class="CC_content">
      <div v-if="loading" class="CC_loading">
        <i class="fas fa-spinner fa-spin"></i>
        <p>Loading compliances...</p>
      </div>

      <div v-else-if="compliances.length === 0" class="CC_empty">
        <i class="fas fa-inbox"></i>
        <p>No compliances selected</p>
      </div>

      <div v-else class="CC_compliances-list">
        <div 
          v-for="(compliance, index) in compliances" 
          :key="index"
          :class="['CC_compliance-card', { 'CC_selected': isSelected(index), 'CC_editing': editingIndex === index }]"
        >
          <div class="CC_card-header">
            <label class="CC_checkbox-label">
              <input 
                type="checkbox" 
                :checked="isSelected(index)"
                @change="toggleSelection(index)"
                class="CC_checkbox"
              />
              <span class="CC_compliance-number">#{{ index + 1 }}</span>
            </label>
            <div class="CC_card-actions">
              <button 
                @click="editCompliance(index)"
                class="CC_edit-button"
                :disabled="editingIndex !== null && editingIndex !== index"
              >
                <i :class="editingIndex === index ? 'fas fa-times' : 'fas fa-edit'"></i>
                {{ editingIndex === index ? 'Cancel' : 'Edit' }}
              </button>
              <button 
                @click="deleteCompliance(index)"
                class="CC_delete-button"
                :disabled="editingIndex !== null"
              >
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>

          <div v-if="editingIndex === index" class="CC_edit-form">
            <div class="CC_form-section">
              <h4>Policy Information</h4>
              <div class="CC_form-grid">
                <div class="CC_form-field">
                  <label>Policy Name *</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.policy.name"
                    required
                  />
                </div>
                <div class="CC_form-field">
                  <label>Policy Identifier</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.policy.identifier"
                  />
                </div>
              </div>
              <div class="CC_form-field">
                <label>Policy Description</label>
                <textarea 
                  v-model="editedCompliance.policy.description"
                  rows="2"
                ></textarea>
              </div>
              <div class="CC_form-grid">
                <div class="CC_form-field">
                  <label>Policy Scope</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.policy.scope"
                  />
                </div>
                <div class="CC_form-field">
                  <label>Policy Objective</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.policy.objective"
                  />
                </div>
              </div>
            </div>

            <div class="CC_form-section">
              <h4>SubPolicy Information</h4>
              <div class="CC_form-grid">
                <div class="CC_form-field">
                  <label>SubPolicy Name *</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.subpolicy.name"
                    required
                  />
                </div>
                <div class="CC_form-field">
                  <label>SubPolicy Identifier</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.subpolicy.identifier"
                  />
                </div>
              </div>
              <div class="CC_form-field">
                <label>SubPolicy Description</label>
                <textarea 
                  v-model="editedCompliance.subpolicy.description"
                  rows="2"
                ></textarea>
              </div>
              <div class="CC_form-field">
                <label>Control</label>
                <input 
                  type="text" 
                  v-model="editedCompliance.subpolicy.control"
                />
              </div>
            </div>

            <div class="CC_form-section">
              <h4>Compliance Information</h4>
              <div class="CC_form-field">
                <label>Compliance Title *</label>
                <input 
                  type="text" 
                  v-model="editedCompliance.compliance.title"
                  required
                />
              </div>
              <div class="CC_form-field">
                <label>Compliance Description *</label>
                <textarea 
                  v-model="editedCompliance.compliance.description"
                  rows="3"
                  required
                ></textarea>
              </div>
              <div class="CC_form-grid">
                <div class="CC_form-field">
                  <label>Compliance Type</label>
                  <input 
                    type="text" 
                    v-model="editedCompliance.compliance.type"
                  />
                </div>
                <div class="CC_form-field">
                  <label>Criticality</label>
                  <select v-model="editedCompliance.compliance.criticality">
                    <option>Low</option>
                    <option>Medium</option>
                    <option>High</option>
                    <option>Critical</option>
                  </select>
                </div>
              </div>
              <div class="CC_form-grid">
                <div class="CC_form-field">
                  <label>Mandatory / Optional</label>
                  <select v-model="editedCompliance.compliance.mandatory">
                    <option>Mandatory</option>
                    <option>Optional</option>
                  </select>
                </div>
                <div class="CC_form-field">
                  <label>Manual / Automatic</label>
                  <select v-model="editedCompliance.compliance.manual_automatic">
                    <option>Manual</option>
                    <option>Automatic</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="CC_form-actions">
              <button @click="saveEdit(index)" class="CC_save-edit-button">
                <i class="fas fa-check"></i>
                Save Changes
              </button>
              <button @click="cancelEdit" class="CC_cancel-edit-button">
                Cancel
              </button>
            </div>
          </div>

          <div v-else class="CC_compliance-details">
            <div class="CC_detail-section">
              <h6>Policy</h6>
              <p><strong>Name:</strong> {{ compliance.policy.name || 'N/A' }}</p>
              <p v-if="compliance.policy.identifier"><strong>Identifier:</strong> {{ compliance.policy.identifier }}</p>
              <p v-if="compliance.policy.description"><strong>Description:</strong> {{ compliance.policy.description }}</p>
            </div>
            <div class="CC_detail-section">
              <h6>SubPolicy</h6>
              <p><strong>Name:</strong> {{ compliance.subpolicy.name || 'N/A' }}</p>
              <p v-if="compliance.subpolicy.identifier"><strong>Identifier:</strong> {{ compliance.subpolicy.identifier }}</p>
              <p v-if="compliance.subpolicy.description"><strong>Description:</strong> {{ compliance.subpolicy.description }}</p>
            </div>
            <div class="CC_detail-section">
              <h6>Compliance</h6>
              <p><strong>Title:</strong> {{ compliance.compliance.title || 'N/A' }}</p>
              <p><strong>Description:</strong> {{ compliance.compliance.description || 'N/A' }}</p>
              <div class="CC_compliance-meta">
                <span v-if="compliance.compliance.type"><strong>Type:</strong> {{ compliance.compliance.type }}</span>
                <span><strong>Criticality:</strong> {{ compliance.compliance.criticality }}</span>
                <span><strong>Mandatory:</strong> {{ compliance.compliance.mandatory }}</span>
                <span><strong>Manual/Automatic:</strong> {{ compliance.compliance.manual_automatic }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import frameworkComparisonService from '@/services/frameworkComparisonService'
import { PopupService } from '@/modules/popup'

export default {
  name: 'ChecklistedCompliances',
  data() {
    return {
      compliances: [],
      selectedCompliances: [],
      editingIndex: null,
      editedCompliance: null,
      loading: false,
      saving: false,
      frameworkId: null
    }
  },
  async mounted() {
    await this.loadCompliances()
  },
  methods: {
    async loadCompliances() {
      this.loading = true
      try {
        // Load from localStorage
        const stored = localStorage.getItem('selected_compliances_for_add')
        const frameworkId = localStorage.getItem('framework_id_for_compliances')
        
        if (!stored) {
          PopupService.warning('No compliances found. Please go back and select compliances.', 'No Data')
          this.goBack()
          return
        }
        
        this.compliances = JSON.parse(stored)
        this.frameworkId = frameworkId ? parseInt(frameworkId) : null
        
        // Initialize selectedCompliances to all indices
        this.selectedCompliances = this.compliances.map((_, index) => index)
      } catch (error) {
        console.error('Error loading compliances:', error)
        PopupService.error('Failed to load compliances. Please try again.', 'Error')
      } finally {
        this.loading = false
      }
    },
    
    isSelected(index) {
      return this.selectedCompliances.includes(index)
    },
    
    toggleSelection(index) {
      const idx = this.selectedCompliances.indexOf(index)
      if (idx > -1) {
        this.selectedCompliances.splice(idx, 1)
      } else {
        this.selectedCompliances.push(index)
      }
    },
    
    selectAll() {
      this.selectedCompliances = this.compliances.map((_, index) => index)
    },
    
    deselectAll() {
      this.selectedCompliances = []
    },
    
    editCompliance(index) {
      if (this.editingIndex === index) {
        this.cancelEdit()
      } else {
        if (this.editingIndex !== null) {
          PopupService.warning('Please save or cancel the current edit first.', 'Edit in Progress')
          return
        }
        this.editingIndex = index
        // Deep copy for editing
        this.editedCompliance = JSON.parse(JSON.stringify(this.compliances[index]))
      }
    },
    
    cancelEdit() {
      this.editingIndex = null
      this.editedCompliance = null
    },
    
    saveEdit(index) {
      // Validate required fields
      if (!this.editedCompliance.policy.name || !this.editedCompliance.subpolicy.name || 
          !this.editedCompliance.compliance.title || !this.editedCompliance.compliance.description) {
        PopupService.warning('Please fill in all required fields (marked with *).', 'Validation Error')
        return
      }
      
      // Update the compliance
      this.compliances[index] = JSON.parse(JSON.stringify(this.editedCompliance))
      this.cancelEdit()
      PopupService.success('Compliance updated successfully.', 'Success')
    },
    
    deleteCompliance(index) {
      PopupService.confirm(
        'Are you sure you want to remove this compliance from the list?',
        'Remove Compliance',
        () => {
          this.compliances.splice(index, 1)
          // Update selected indices
          this.selectedCompliances = this.selectedCompliances
            .filter(idx => idx !== index)
            .map(idx => idx > index ? idx - 1 : idx)
          PopupService.success('Compliance removed from list.', 'Removed')
        },
        () => {}
      )
    },
    
    async saveSelectedCompliances() {
      if (this.selectedCompliances.length === 0) {
        PopupService.warning('Please select at least one compliance to save.', 'No Selection')
        return
      }
      
      if (!this.frameworkId) {
        PopupService.error('Framework ID not found. Please go back and try again.', 'Error')
        return
      }
      
      this.saving = true
      let successCount = 0
      let errorCount = 0
      
      try {
        // Save each selected compliance
        for (const index of this.selectedCompliances) {
          try {
            const compliance = this.compliances[index]
            await frameworkComparisonService.createComplianceFromAmendment(
              this.frameworkId,
              compliance
            )
            successCount++
          } catch (error) {
            console.error(`Error saving compliance ${index + 1}:`, error)
            errorCount++
          }
        }
        
        if (successCount > 0) {
          PopupService.success(
            `Successfully saved ${successCount} compliance(s).${errorCount > 0 ? ` ${errorCount} failed.` : ''}`,
            'Save Complete'
          )
          
          // Remove saved compliances from list
          const indicesToRemove = [...this.selectedCompliances].sort((a, b) => b - a)
          indicesToRemove.forEach(idx => {
            this.compliances.splice(idx, 1)
          })
          this.selectedCompliances = []
          
          // Update localStorage
          localStorage.setItem('selected_compliances_for_add', JSON.stringify(this.compliances))
          
          // If no more compliances, go back
          if (this.compliances.length === 0) {
            setTimeout(() => {
              this.goBack()
            }, 2000)
          }
        } else {
          PopupService.error('Failed to save any compliances. Please try again.', 'Save Failed')
        }
      } catch (error) {
        console.error('Error saving compliances:', error)
        PopupService.error('An error occurred while saving. Please try again.', 'Error')
      } finally {
        this.saving = false
      }
    },
    
    goBack() {
      this.$router.push('/framework-migration/comparison')
    }
  }
}
</script>

<style scoped>
.CC_container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  margin-left: 280px;
}

.CC_header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.CC_back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--secondary-color, #f3f4f6);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-primary, #111827);
  font-size: 14px;
}

.CC_back-button:hover {
  background: var(--border-color, #e5e7eb);
}

.CC_header h2 {
  margin: 0;
  flex: 1;
  font-size: 24px;
  font-weight: 600;
}

.CC_header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.CC_action-button,
.CC_save-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.CC_action-button {
  background: var(--secondary-color, #f3f4f6);
  border-color: var(--border-color, #e5e7eb);
  color: var(--text-primary, #111827);
}

.CC_action-button:hover {
  background: var(--border-color, #e5e7eb);
}

.CC_save-button {
  background: var(--primary-color, #3b82f6);
  border-color: var(--primary-color, #3b82f6);
  color: white;
}

.CC_save-button:hover:not(:disabled) {
  background: var(--primary-color-dark, #2563eb);
  opacity: 0.9;
}

.CC_save-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.CC_content {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 24px;
}

.CC_loading,
.CC_empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary, #6b7280);
}

.CC_loading i,
.CC_empty i {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--text-secondary, #6b7280);
}

.CC_compliances-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.CC_compliance-card {
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  padding: 20px;
  background: var(--card-bg, #fff);
  transition: all 0.2s;
}

.CC_compliance-card.CC_selected {
  border-color: var(--primary-color, #3b82f6);
  background: rgba(59, 130, 246, 0.05);
}

.CC_compliance-card.CC_editing {
  border-color: var(--warning-color, #f59e0b);
}

.CC_card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.CC_checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.CC_checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.CC_compliance-number {
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.CC_card-actions {
  display: flex;
  gap: 8px;
}

.CC_edit-button,
.CC_delete-button {
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.CC_edit-button {
  background: var(--secondary-color, #f3f4f6);
  border-color: var(--border-color, #e5e7eb);
  color: var(--text-primary, #111827);
}

.CC_edit-button:hover:not(:disabled) {
  background: var(--border-color, #e5e7eb);
}

.CC_delete-button {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.CC_delete-button:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.2);
}

.CC_edit-form {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.CC_form-section {
  margin-bottom: 24px;
}

.CC_form-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.CC_form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.CC_form-field {
  margin-bottom: 16px;
}

.CC_form-field label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #111827);
}

.CC_form-field input,
.CC_form-field textarea,
.CC_form-field select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.CC_form-field textarea {
  resize: vertical;
}

.CC_form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.CC_save-edit-button,
.CC_cancel-edit-button {
  padding: 10px 20px;
  border-radius: 6px;
  border: 1px solid;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.CC_save-edit-button {
  background: var(--primary-color, #3b82f6);
  border-color: var(--primary-color, #3b82f6);
  color: white;
}

.CC_save-edit-button:hover {
  background: var(--primary-color-dark, #2563eb);
}

.CC_cancel-edit-button {
  background: var(--secondary-color, #f3f4f6);
  border-color: var(--border-color, #e5e7eb);
  color: var(--text-primary, #111827);
}

.CC_cancel-edit-button:hover {
  background: var(--border-color, #e5e7eb);
}

.CC_compliance-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.CC_detail-section {
  padding: 12px;
  background: var(--secondary-color, #f9fafb);
  border-radius: 6px;
}

.CC_detail-section h6 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.CC_detail-section p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--text-secondary, #6b7280);
}

.CC_detail-section strong {
  color: var(--text-primary, #111827);
}

.CC_compliance-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.CC_compliance-meta span {
  font-size: 12px;
  color: var(--text-secondary, #6b7280);
}

@media (max-width: 768px) {
  .CC_container {
    margin-left: 0;
    padding: 16px;
  }
  
  .CC_form-grid {
    grid-template-columns: 1fr;
  }
  
  .CC_header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .CC_header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>










