<template>
  <div class="document-handling-container">
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-file-alt"></i>
        Document Handling
      </h1>
      <p class="page-subtitle">Manage and view all uploaded documents across modules</p>
    </div>

    <!-- Upload Section -->
    <div class="upload-section">
      <div class="upload-header">
        <h3>
          <i class="fas fa-cloud-upload-alt"></i>
          Upload Document
        </h3>
        <p v-if="activeModule === 'companyFolders' && uploadCompany" class="upload-destination-hint">
          <i class="fas fa-folder"></i>
          Uploads will go to: <strong>{{ uploadCompanyName }}</strong><span v-if="uploadSubfolder"> / {{ uploadSubfolderName }}</span>
        </p>
      </div>
      <div class="upload-form">
        <div class="form-row">
          <div class="form-group">
            <label for="file-input">
              <i class="fas fa-file"></i> Select File
            </label>
            <input 
              type="file" 
              id="file-input"
              ref="fileInput"
              @change="handleFileSelect"
              class="file-input"
              accept=".pdf,.doc,.docx,.xlsx,.xls,.csv,.txt"
            />
            <button @click="triggerFileInput" class="file-select-btn">
              <i class="fas fa-folder-open"></i>
              {{ selectedFile ? selectedFile.name : 'Choose File' }}
            </button>
          </div>

          <div class="form-group">
            <label for="module-select">
              <i class="fas fa-cubes"></i> Module *
            </label>
            <select v-model="uploadModule" id="module-select" class="form-select">
              <option value="">-- Select Module --</option>
              <option value="policy">Policy</option>
              <option value="audit">Audit</option>
              <option value="incident">Incident</option>
              <option value="risk">Risk</option>
            </select>
          </div>

          <div class="form-group">
            <label for="framework-select">
              <i class="fas fa-sitemap"></i> Framework (Optional)
            </label>
            <select v-model="uploadFramework" id="framework-select" class="form-select">
              <option value="">-- No Framework --</option>
              <option
                v-for="fw in frameworks"
                :key="fw.FrameworkId"
                :value="fw.FrameworkName"
              >
                {{ fw.FrameworkName }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="company-select">
              <i class="fas fa-building"></i> Company (Optional)
            </label>
            <select v-model="uploadCompany" id="company-select" class="form-select">
              <option value="">-- No Company --</option>
              <option
                v-for="company in companyFolders"
                :key="company.id"
                :value="company.code"
              >
                {{ company.name }}
              </option>
            </select>
          </div>

          <div v-if="uploadCompany" class="form-group">
            <label for="subfolder-select">
              <i class="fas fa-folder"></i> Folder in Company (Optional)
            </label>
            <select v-model="uploadSubfolder" id="subfolder-select" class="form-select">
              <option value="">-- Root (no subfolder) --</option>
              <option
                v-for="sub in uploadCompanySubfolders"
                :key="sub.id"
                :value="sub.code"
              >
                {{ sub.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <button 
              @click="uploadDocument" 
              :disabled="!selectedFile || !uploadModule || uploading"
              class="upload-btn"
            >
              <i :class="uploading ? 'fas fa-spinner fa-spin' : 'fas fa-cloud-upload-alt'"></i>
              {{ uploading ? 'Uploading...' : 'Upload Document' }}
            </button>
          </div>
        </div>

        <!-- Upload Progress -->
        <div v-if="uploadProgress" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <span class="progress-text">{{ uploadProgress }}%</span>
        </div>

        <!-- Upload Status Message -->
        <div v-if="uploadMessage" :class="['upload-message', uploadMessageType]">
          <i :class="uploadMessageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
          {{ uploadMessage }}
        </div>
      </div>
    </div>

    <!-- Background Fetch Indicator -->
    <div v-if="isBackgroundFetching" class="background-fetch-indicator">
      <i class="fas fa-sync fa-spin"></i>
      Loading documents in background...
    </div>

    <!-- Module Tabs -->
    <div class="module-tabs">
      <button 
        v-for="module in modules" 
        :key="module.id"
        @click="activeModule = module.id"
        :class="['tab-button', { active: activeModule === module.id }]"
      >
        <i :class="module.icon"></i>
        {{ module.name }}
        <span class="document-count">({{ getDocumentCount(module.id) }})</span>
      </button>
    </div>

    <!-- Document List -->
    <div class="document-list-container">
      <div class="list-header">
        <h2>
          <!-- For Company Folders, don't append 'Documents' to the main heading -->
          <span v-if="activeModule === 'companyFolders'">
            {{ getActiveModuleName() }}
          </span>
          <span v-else>
            {{ getActiveModuleName() }}{{ activeModule !== 'all' ? ' Documents' : '' }}
          </span>
        </h2>
        <div class="list-actions">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search documents..."
              class="search-input"
            />
          </div>

          <!-- Company selector in top-right when in Company Folders tab -->
          <div
            v-if="activeModule === 'companyFolders'"
            class="filter-dropdown"
          >
            <select
              v-model="selectedCompanyForDocs"
              @change="loadCompanyDocuments"
              class="filter-select"
            >
              <option value="">-- Select Company --</option>
              <option
                v-for="company in companyFolders"
                :key="company.id"
                :value="company.code"
              >
                {{ company.name }}
              </option>
            </select>
          </div>

          <div
            v-else
            class="filter-dropdown"
          >
            <select v-model="selectedFilter" class="filter-select">
              <option value="all">All Documents</option>
              <option value="pdf">PDF Files</option>
              <option value="doc">DOC Files</option>
              <option value="docx">DOCX Files</option>
              <option value="xlsx">Excel Files</option>
              <option value="csv">CSV Files</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Company Folders Management -->
      <div v-if="activeModule === 'companyFolders'" class="company-folders-section">
        <div class="company-folders-form">
          <div class="form-row">
            <div class="form-group">
              <label for="company-name-input">
                <i class="fas fa-building"></i> Company Folder Name
              </label>
              <input
                id="company-name-input"
                v-model="newCompanyName"
                type="text"
                class="form-input"
                placeholder="Enter company folder name"
              />
            </div>
            <div class="form-group">
              <label for="company-description-input">
                <i class="fas fa-align-left"></i> Description (Optional)
              </label>
              <input
                id="company-description-input"
                v-model="newCompanyDescription"
                type="text"
                class="form-input"
                placeholder="Short description"
              />
            </div>
            <div class="form-group">
              <button
                @click="createCompanyFolder"
                :disabled="creatingCompanyFolder || !newCompanyName"
                class="upload-btn"
              >
                <i :class="creatingCompanyFolder ? 'fas fa-spinner fa-spin' : 'fas fa-plus'"></i>
                {{ creatingCompanyFolder ? 'Creating...' : 'Create Company Folder' }}
              </button>
            </div>
          </div>
          <div v-if="companyMessage" :class="['upload-message', companyMessageType]">
            <i :class="companyMessageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
            {{ companyMessage }}
          </div>
        </div>

        <div class="document-table">
          <div class="table-header">
            <div class="header-cell name-cell">Company Folder</div>
            <div class="header-cell module-cell">Code</div>
            <div class="header-cell person-cell">Description</div>
            <div class="header-cell time-cell">Files</div>
          </div>
          <div class="table-body">
            <div
              v-for="company in companyFolders"
              :key="company.id"
              class="table-row"
              @click="() => { selectedCompanyForDocs = company.code; selectedCompanyId = company.id; loadCompanyDocuments(); loadCompanySubfolders(company.id); syncUploadToSelectedFolder(); }"
            >
              <div class="table-cell name-cell">
                <div class="document-info">
                  <i class="fas fa-folder-open file-icon"></i>
                  <span class="document-name">{{ company.name }}</span>
                </div>
              </div>
              <div class="table-cell module-cell">
                <span class="module-badge">
                  {{ company.code }}
                </span>
              </div>
              <div class="table-cell person-cell">
                <span class="user-name">{{ company.description || '—' }}</span>
              </div>
              <div class="table-cell time-cell">
                <span class="upload-time">{{ company.document_count ?? 0 }}</span>
              </div>
            </div>
          </div>

          <div
            v-if="companyFolders.length === 0"
            class="empty-state"
          >
            <i class="fas fa-folder-open empty-icon"></i>
            <h3>No company folders yet</h3>
            <p>Create your first company folder using the form above.</p>
          </div>
        </div>

        <!-- Folders inside selected company -->
        <div v-if="activeCompanyCode && selectedCompanyId" class="company-subfolders-section">
          <div class="list-header">
            <h3>
              Folders in {{ selectedCompanyName }}
            </h3>
          </div>
          <div class="company-folders-form">
            <div class="form-row">
              <div class="form-group">
                <label for="subfolder-name-input">
                  <i class="fas fa-folder"></i> Folder name
                </label>
                <input
                  id="subfolder-name-input"
                  v-model="newSubfolderName"
                  type="text"
                  class="form-input"
                  placeholder="e.g. Policies, Contracts"
                />
              </div>
              <div class="form-group">
                <button
                  @click="createCompanySubfolder"
                  :disabled="creatingSubfolder || !newSubfolderName"
                  class="upload-btn"
                >
                  <i :class="creatingSubfolder ? 'fas fa-spinner fa-spin' : 'fas fa-plus'"></i>
                  {{ creatingSubfolder ? 'Creating...' : 'Create Folder' }}
                </button>
              </div>
            </div>
            <div v-if="subfolderMessage" :class="['upload-message', subfolderMessageType]">
              <i :class="subfolderMessageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
              {{ subfolderMessage }}
            </div>
          </div>
          <div class="document-table">
            <div class="table-header">
              <div class="header-cell name-cell">Folder</div>
              <div class="header-cell module-cell">Code</div>
              <div class="header-cell time-cell">Files</div>
              <div class="header-cell actions-cell">Actions</div>
            </div>
            <div class="table-body">
              <div
                class="table-row"
                :class="{ active: !selectedSubfolderCode }"
                @click="() => { selectedSubfolderCode = ''; syncUploadToSelectedFolder(); }"
              >
                <div class="table-cell name-cell">
                  <div class="document-info">
                    <i class="fas fa-folder-open file-icon"></i>
                    <span class="document-name">All documents in company</span>
                  </div>
                </div>
                <div class="table-cell module-cell">—</div>
                <div class="table-cell time-cell">{{ companyFolderDocCount }}</div>
                <div class="table-cell actions-cell">—</div>
              </div>
              <div
                v-for="sub in companySubfolders"
                :key="sub.id"
                class="table-row"
                :class="{ active: selectedSubfolderCode === sub.code }"
                @click="() => { selectedSubfolderCode = sub.code; syncUploadToSelectedFolder(); }"
              >
                <div class="table-cell name-cell">
                  <div class="document-info">
                    <i class="fas fa-folder file-icon"></i>
                    <span class="document-name">{{ sub.name }}</span>
                  </div>
                </div>
                <div class="table-cell module-cell">
                  <span class="module-badge">{{ sub.code }}</span>
                </div>
                <div class="table-cell time-cell">{{ sub.document_count ?? 0 }}</div>
              </div>
            </div>
            <div v-if="companySubfolders.length === 0 && !selectedSubfolderCode" class="empty-state small">
              <p>No subfolders yet. Create one above to organize files.</p>
            </div>
          </div>
        </div>

        <!-- Documents for selected company -->
        <div class="company-documents-section">
          <div class="list-header">
            <h3>
              Documents for Company
              <span v-if="selectedSubfolderCode"> / {{ selectedSubfolderName }}</span>
              <span v-if="activeCompanyCode && filteredDocuments.length">
                ({{ filteredDocuments.length }})
              </span>
            </h3>
          </div>

          <div v-if="activeCompanyCode" class="document-table">
            <div class="table-header">
              <div class="header-cell name-cell">Document Name</div>
              <div class="header-cell time-cell">Upload Time</div>
              <div class="header-cell person-cell">Uploaded By</div>
              <div class="header-cell module-cell">Module</div>
            </div>

            <div class="table-body">
              <div
                v-for="document in filteredDocuments"
                :key="document.id"
                class="table-row"
              >
                <div class="table-cell name-cell">
                  <div class="document-info" @click="openDocument(document)">
                    <i :class="getFileIcon(document.fileType)" class="file-icon"></i>
                    <span class="document-name">{{ document.name }}</span>
                  </div>
                </div>
                <div class="table-cell time-cell">
                  <span class="upload-time">{{ formatDate(document.uploadTime) }}</span>
                </div>
                <div class="table-cell person-cell">
                  <div class="user-info">
                    <span class="user-name">{{ document.uploadedBy }}</span>
                  </div>
                </div>
                <div class="table-cell module-cell">
                  <span class="module-badge" :class="document.module.toLowerCase()">
                    {{ document.module }}
                  </span>
                </div>
              </div>
            </div>

            <div
              v-if="filteredDocuments.length === 0 && !isBackgroundFetching"
              class="empty-state"
            >
              <i class="fas fa-file-alt empty-icon"></i>
              <h3>No documents found for this company</h3>
              <p>Try uploading a document with this company selected.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Error State (only show if critical error) -->
      <div
        v-if="error && !isBackgroundFetching && documents.length === 0 && activeModule !== 'companyFolders'"
        class="error-state"
      >
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Documents</h3>
        <p>{{ error }}</p>
        <button @click="() => fetchDocuments(1)" class="btn btn-primary">
          <i class="fas fa-redo"></i> Retry
        </button>
      </div>

      <!-- Document table (hidden when managing company folders) -->
      <div v-if="activeModule !== 'companyFolders'" class="document-table">
        <div class="table-header">
          <div class="header-cell name-cell">Document Name</div>
          <div class="header-cell time-cell">Upload Time</div>
          <div class="header-cell person-cell">Uploaded By</div>
          <div class="header-cell module-cell">Module</div>
        </div>

        <div class="table-body">
          <div 
            v-for="document in filteredDocuments" 
            :key="document.id"
            class="table-row"
          >
            <div class="table-cell name-cell">
              <div class="document-info" @click="openDocument(document)">
                <i :class="getFileIcon(document.fileType)" class="file-icon"></i>
                <span class="document-name">{{ document.name }}</span>
              </div>
            </div>
            <div class="table-cell time-cell">
              <span class="upload-time">{{ formatDate(document.uploadTime) }}</span>
            </div>
            <div class="table-cell person-cell">
              <div class="user-info">
                <span class="user-name">{{ document.uploadedBy }}</span>
              </div>
            </div>
            <div class="table-cell module-cell">
              <span class="module-badge" :class="document.module.toLowerCase()">
                {{ document.module }}
              </span>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="filteredDocuments.length === 0 && !isBackgroundFetching" class="empty-state">
          <i class="fas fa-file-alt empty-icon"></i>
          <h3>No documents found</h3>
          <p v-if="!searchQuery">{{ error || 'No documents have been uploaded yet. Upload your first document above!' }}</p>
          <p v-else>No documents match your current search criteria.</p>
        </div>
        
        <!-- Loading State (Background) -->
        <div v-if="filteredDocuments.length === 0 && isBackgroundFetching" class="empty-state">
          <i class="fas fa-sync fa-spin empty-icon"></i>
          <h3>Loading documents...</h3>
          <p>Fetching your documents from the server. This won't take long!</p>
        </div>
      </div>

      <!-- Pagination Controls -->
      <div v-if="totalPages > 1 && !isBackgroundFetching" class="pagination-container">
        <div class="pagination-info">
          <span>Showing {{ (currentPage - 1) * pageSize + 1 }} to {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} documents</span>
        </div>
        <div class="pagination-controls">
          <button 
            @click="prevPage" 
            :disabled="currentPage === 1"
            class="pagination-btn"
            :class="{ disabled: currentPage === 1 }"
          >
            <i class="fas fa-chevron-left"></i> Previous
          </button>
          
          <div class="pagination-pages">
            <button
              v-for="pageNum in getVisiblePages()"
              :key="pageNum"
              @click="goToPage(pageNum)"
              class="pagination-page-btn"
              :class="{ active: pageNum === currentPage }"
            >
              {{ pageNum }}
            </button>
          </div>
          
          <button 
            @click="nextPage" 
            :disabled="currentPage === totalPages"
            class="pagination-btn"
            :class="{ disabled: currentPage === totalPages }"
          >
            Next <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Document Details Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Document Details</h3>
          <button @click="closeModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body" v-if="selectedDocument">
          <div class="detail-row">
            <label>Document Name:</label>
            <span>{{ selectedDocument.name }}</span>
          </div>
          <div class="detail-row">
            <label>File Type:</label>
            <span>{{ selectedDocument.fileType.toUpperCase() }}</span>
          </div>
          <div class="detail-row">
            <label>File Size:</label>
            <span>{{ selectedDocument.fileSize }}</span>
          </div>
          <div class="detail-row">
            <label>Uploaded By:</label>
            <span>{{ selectedDocument.uploadedBy }}</span>
          </div>
          <div class="detail-row">
            <label>Upload Time:</label>
            <span>{{ formatDate(selectedDocument.uploadTime) }}</span>
          </div>
          <div class="detail-row">
            <label>Module:</label>
            <span class="module-badge" :class="selectedDocument.module.toLowerCase()">
              {{ selectedDocument.module }}
            </span>
          </div>
          <div class="detail-row">
            <label>Description:</label>
            <span>{{ selectedDocument.description || 'No description available' }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="openDocument(selectedDocument)" class="btn btn-primary">
            <i class="fas fa-eye"></i> View Document
          </button>
          <button @click="downloadDocument(selectedDocument)" class="btn btn-secondary">
            <i class="fas fa-download"></i> Download
          </button>
          <button @click="closeModal" class="btn btn-cancel">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { API_ENDPOINTS, axiosInstance } from '@/config/api'
import documentDataService from '@/services/documentService'
import './DocumentHandling.css'
import './background-fetch.css'

export default {
  name: 'DocumentHandling',
  setup() {
    const activeModule = ref('all')
    const searchQuery = ref('')
    const selectedFilter = ref('all')
    const showModal = ref(false)
    const selectedDocument = ref(null)
    // NEVER show loading spinner - always load instantly
    const loading = ref(false)
    const error = ref(null)
    const isBackgroundFetching = ref(false)
    
    // Pagination state
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalPages = ref(0)
    const totalCount = ref(0)
    
    // Upload form state
    const selectedFile = ref(null)
    const uploadModule = ref('')
    const uploadFramework = ref('')
    const uploadCompany = ref('')
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const uploadMessage = ref('')
    const uploadMessageType = ref('success')
    const fileInput = ref(null)
    const frameworks = ref([])
    const companyFolders = ref([])
    const activeCompanyCode = ref('')
    const selectedCompanyForDocs = ref('')
    const selectedCompanyId = ref(null)
    const companySubfolders = ref([])
    const selectedSubfolderCode = ref('')
    const newSubfolderName = ref('')
    const creatingSubfolder = ref(false)
    const subfolderMessage = ref('')
    const subfolderMessageType = ref('success')
    const uploadSubfolder = ref('')
    const uploadCompanySubfolders = ref([])
    const newCompanyName = ref('')
    const newCompanyDescription = ref('')
    const creatingCompanyFolder = ref(false)
    const companyMessage = ref('')
    const companyMessageType = ref('success')
    const deletingFolderId = ref(null)
    const deletingSubfolderId = ref(null)
    const deletingDocId = ref(null)

    const SYNTHETIC_MODULE = 'synthetic'
    const isSyntheticModule = (moduleName) => (moduleName || '').toLowerCase() === SYNTHETIC_MODULE
    const sanitizeDocuments = (docs = []) => docs.filter(doc => !isSyntheticModule(doc.module))
    const createEmptyCounts = () => ({
      all: 0,
      policy: 0,
      audit: 0,
      incident: 0,
      risk: 0,
      event: 0
    })

    // Module definitions
    const modules = ref([
      { id: 'all', name: 'All Documents', icon: 'fas fa-folder-open' },
      { id: 'policy', name: 'Policy', icon: 'fas fa-file-alt' },
      { id: 'audit', name: 'Audit', icon: 'fas fa-clipboard-check' },
      { id: 'incident', name: 'Incident', icon: 'fas fa-exclamation-circle' },
      { id: 'risk', name: 'Risk', icon: 'fas fa-exclamation-triangle' },
      { id: 'event', name: 'Event', icon: 'fas fa-calendar-alt' },
      { id: 'companyFolders', name: 'Company Folders', icon: 'fas fa-building' }
    ])

    // Document data from service - Load from cache IMMEDIATELY
    const cachedDocuments = sanitizeDocuments(documentDataService.getData('documents') || [])
    const cachedCounts = documentDataService.getData('documentCounts') || createEmptyCounts()
    
    const documents = ref(cachedDocuments)
    const documentCounts = ref(cachedCounts)
    
    // Log cache status - IMMEDIATE
    console.log('[DocumentHandling] ⚡ Component setup START - Loading INSTANTLY')
    console.log('[DocumentHandling] 📊 Cache status:', {
      hasCachedDocs: cachedDocuments.length > 0,
      cachedDocsCount: cachedDocuments.length,
      counts: cachedCounts
    })
    console.log('[DocumentHandling] ✅ Page will display in <50ms - NO BLOCKING!')

    // Load all frameworks from backend (show complete list from DB)
    const loadFrameworks = async () => {
      try {
        // Fetch all frameworks (including all statuses) so user can see everything
        const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORKS, {
          params: { include_all_status: true },
        })

        // Backend returns a plain list of frameworks
        const data = Array.isArray(response.data)
          ? response.data
          : (response.data?.data || [])

        frameworks.value = data
        console.log('[DocumentHandling] ✅ Loaded frameworks for upload dropdown:', frameworks.value.length)
      } catch (err) {
        console.error('[DocumentHandling] ❌ Error loading frameworks for upload dropdown:', err)
      }
    }

    const loadCompanyFolders = async () => {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.COMPANY_FOLDERS)
        if (response.data && response.data.success) {
          companyFolders.value = response.data.folders || []
          console.log('[DocumentHandling] ✅ Loaded company folders:', companyFolders.value.length)
        } else {
          companyFolders.value = []
        }
      } catch (err) {
        console.error('[DocumentHandling] ❌ Error loading company folders:', err)
      }
    }

    const loadCompanySubfolders = async (folderId) => {
      if (!folderId) {
        companySubfolders.value = []
        return
      }
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.COMPANY_SUBFOLDERS(folderId))
        if (response.data && response.data.success) {
          companySubfolders.value = response.data.subfolders || []
        } else {
          companySubfolders.value = []
        }
      } catch (err) {
        console.error('[DocumentHandling] ❌ Error loading company subfolders:', err)
        companySubfolders.value = []
      }
    }

    const loadUploadCompanySubfolders = async () => {
      if (!uploadCompany.value) {
        uploadCompanySubfolders.value = []
        return
      }
      const company = companyFolders.value.find(c => c.code === uploadCompany.value)
      if (!company) {
        uploadCompanySubfolders.value = []
        return
      }
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.COMPANY_SUBFOLDERS(company.id))
        if (response.data && response.data.success) {
          uploadCompanySubfolders.value = response.data.subfolders || []
        } else {
          uploadCompanySubfolders.value = []
        }
      } catch (err) {
        console.error('[DocumentHandling] ❌ Error loading upload subfolders:', err)
        uploadCompanySubfolders.value = []
      }
    }

    // Fetch documents from API (for filtering/searching) - Non-blocking with pagination
    const fetchDocuments = async (page = 1) => {
      try {
        // Don't show loading spinner - keep page interactive
        isBackgroundFetching.value = true
        error.value = null
        
        console.log('[DocumentHandling] 🔍 Fetching documents (page', page, ')...')
        
        // Build query parameters with pagination
        const params = {
          module: activeModule.value === 'companyFolders' ? 'all' : activeModule.value,
          search: searchQuery.value,
          file_type: selectedFilter.value,
          page: page,
          page_size: pageSize.value
        }

        // When in Company Folders, send company and optional subfolder so backend can return prefix-based + linked docs (e.g. AI audit evidence)
        if (activeCompanyCode.value) {
          params.company_code = activeCompanyCode.value
          if (selectedSubfolderCode.value) {
            params.subfolder_code = selectedSubfolderCode.value
          }
        }
        
        const response = await axiosInstance.get(API_ENDPOINTS.DOCUMENTS_LIST, { params })
        
        if (response.data.success) {
          const sanitizedDocs = sanitizeDocuments(response.data.documents)
          documents.value = sanitizedDocs
          
          // Update pagination metadata
          currentPage.value = response.data.page || page
          totalPages.value = response.data.total_pages || 0
          totalCount.value = response.data.total_count || 0
          
          // Update cache with filtered results
          documentDataService.setData('documents', sanitizedDocs)
          console.log(`✅ Documents fetched: ${documents.value.length} (page ${currentPage.value} of ${totalPages.value})`)
        } else {
          error.value = 'Failed to load documents'
          console.error('❌ Error loading documents:', response.data.error)
        }
      } catch (err) {
        error.value = 'Failed to fetch documents from server'
        console.error('❌ Error fetching documents:', err)
      } finally {
        isBackgroundFetching.value = false
      }
    }
    
    // Pagination handlers
    const goToPage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
        fetchDocuments(page)
      }
    }
    
    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        goToPage(currentPage.value + 1)
      }
    }
    
    const prevPage = () => {
      if (currentPage.value > 1) {
        goToPage(currentPage.value - 1)
      }
    }

    // Fetch document counts
    const fetchDocumentCounts = async () => {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.DOCUMENTS_COUNTS)
        
        if (response.data.success) {
          const counts = { ...createEmptyCounts(), ...(response.data.counts || {}) }
          documentCounts.value = counts
          // Update cache
          documentDataService.setData('documentCounts', counts)
        }
      } catch (err) {
        console.error('❌ Error fetching document counts:', err)
      }
    }

    // Track if component is mounted
    const isMounted = ref(false)

    // Watch for changes to trigger re-fetch (skip on initial mount)
    watch([activeModule, searchQuery, selectedFilter], () => {
      if (isMounted.value) {
        if (activeModule.value !== 'companyFolders') {
          activeCompanyCode.value = ''
          selectedCompanyForDocs.value = ''
          selectedCompanyId.value = null
          selectedSubfolderCode.value = ''
        }
        console.log('🔍 Filter changed, fetching documents...')
        currentPage.value = 1 // Reset to first page when filters change
        fetchDocuments(1)
      }
    })
    // When subfolder selection changes in Company Folders, refetch so backend returns linked docs (e.g. AI audit evidence)
    watch(selectedSubfolderCode, () => {
      if (isMounted.value && activeModule.value === 'companyFolders' && activeCompanyCode.value) {
        currentPage.value = 1
        fetchDocuments(1)
      }
    })
    watch(uploadCompany, () => {
      uploadSubfolder.value = ''
      loadUploadCompanySubfolders()
    })

    // Initial load - ALWAYS instant, no blocking
    onMounted(() => {
      console.log('📄 Document Handling component mounted - INSTANT DISPLAY')
      
      // Check if user is authenticated before loading documents
      const isAuthenticated = localStorage.getItem('is_logged_in') === 'true' && 
                             localStorage.getItem('access_token') !== null
      
      if (!isAuthenticated) {
        console.warn('[DocumentHandling] ⚠️ User not authenticated, skipping document load')
        error.value = 'Please log in to view documents'
        isMounted.value = true
        return
      }
      
      // Load immediately (non-blocking) - only after authentication check
      // Use pagination for initial load
      fetchDocuments(1)
      
      // Fetch document counts for all modules
      fetchDocumentCounts()

      // Load full framework list for the upload dropdown
      loadFrameworks()

      // Load company folders for dropdown and management tab
      loadCompanyFolders()
      
      // Mark as mounted
      isMounted.value = true
      
      console.log('[DocumentHandling] 🚀 Component ready - page displayed instantly!')
    })

    // Computed properties
    const selectedCompanyName = computed(() => {
      const c = companyFolders.value.find(f => f.code === activeCompanyCode.value)
      return c ? c.name : ''
    })
    const selectedSubfolderName = computed(() => {
      const s = companySubfolders.value.find(f => f.code === selectedSubfolderCode.value)
      return s ? s.name : ''
    })
    const uploadCompanyName = computed(() => {
      const c = companyFolders.value.find(f => f.code === uploadCompany.value)
      return c ? c.name : uploadCompany.value || ''
    })
    const uploadSubfolderName = computed(() => {
      const s = uploadCompanySubfolders.value.find(f => f.code === uploadSubfolder.value)
      return s ? s.name : uploadSubfolder.value || ''
    })
    const companyFolderDocCount = computed(() => {
      if (!activeCompanyCode.value) return 0
      const prefix = (activeCompanyCode.value || '').toLowerCase()
      return documents.value.filter(doc =>
        (doc.name || '').toLowerCase().startsWith(prefix) ||
        (doc.s3Key || '').toLowerCase().startsWith(prefix)
      ).length
    })
    const filteredDocuments = computed(() => {
      // Backend now returns the correct set when company_code (and optional subfolder_code) are sent,
      // including docs linked via CompanySubfolderDocument (e.g. AI audit evidence). No client-side filter needed.
      return documents.value
    })

    // Methods
    const getDocumentCount = (moduleId) => {
      if (moduleId === 'companyFolders') {
        // Show number of company folders instead of documents
        return companyFolders.value.length
      }
      return documentCounts.value[moduleId] || 0
    }

    const getActiveModuleName = () => {
      const module = modules.value.find(m => m.id === activeModule.value)
      return module ? module.name : 'All Documents'
    }
    
    const getVisiblePages = () => {
      const pages = []
      const maxVisible = 5
      let startPage = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
      let endPage = Math.min(totalPages.value, startPage + maxVisible - 1)
      
      // Adjust start if we're near the end
      if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1)
      }
      
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i)
      }
      
      return pages
    }

    const getFileIcon = (fileType) => {
      const icons = {
        pdf: 'fas fa-file-pdf',
        doc: 'fas fa-file-word',
        docx: 'fas fa-file-word',
        xlsx: 'fas fa-file-excel',
        xls: 'fas fa-file-excel',
        csv: 'fas fa-file-csv',
        txt: 'fas fa-file-alt',
        jpg: 'fas fa-file-image',
        png: 'fas fa-file-image'
      }
      return icons[fileType] || 'fas fa-file'
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const openDocument = async (document) => {
      // Always use backend for a short-lived URL; direct S3 URLs fail for private buckets
      if (!document.id) {
        console.error('❌ Cannot open document without ID:', document)
        alert('Document identifier missing; cannot open document')
        return
      }

      try {
        console.log('📂 Requesting secure view URL for document:', document.id, document.name)
        const response = await axiosInstance.get(
          API_ENDPOINTS.DOCUMENTS_DOWNLOAD(document.id),
          { params: { disposition: 'inline' } }
        )

        if (response.data && response.data.success && response.data.downloadUrl) {
          console.log('📂 Opening document from secure URL')
          window.open(response.data.downloadUrl, '_blank')
        } else {
          console.error('❌ Failed to get secure URL for document:', document, response.data)
          alert('Unable to open document: No download URL available')
        }
      } catch (err) {
        console.error('❌ Error getting secure URL for document:', document, err)
        alert('Error while opening document. Please try again.')
      }
    }

    const loadCompanyDocuments = () => {
      if (!selectedCompanyForDocs.value) {
        activeCompanyCode.value = ''
        selectedCompanyId.value = null
        selectedSubfolderCode.value = ''
        return
      }
      activeCompanyCode.value = selectedCompanyForDocs.value
      const company = companyFolders.value.find(c => c.code === selectedCompanyForDocs.value)
      selectedCompanyId.value = company ? company.id : null
      if (company) {
        loadCompanySubfolders(company.id)
      } else {
        companySubfolders.value = []
      }
      selectedSubfolderCode.value = ''
      syncUploadToSelectedFolder()
      console.log('[DocumentHandling] 🔍 Filtering documents for company code:', activeCompanyCode.value)
    }

    // When viewing a company/subfolder in Company Folders tab, set upload form so next upload goes there
    const syncUploadToSelectedFolder = () => {
      if (activeModule.value !== 'companyFolders') return
      if (!activeCompanyCode.value) return
      uploadCompany.value = activeCompanyCode.value
      loadUploadCompanySubfolders().then(() => {
        uploadSubfolder.value = selectedSubfolderCode.value || ''
      })
    }

    const downloadDocument = async (document) => {
      // Prefer legacy direct S3 URL when present (backwards compatibility)
      // Prefer secure URL; raw s3Url often fails for private buckets
      if (document.s3Url && !document.id) {
        console.log('⬇️ Downloading document (legacy URL, no id):', document.name)
        const link = window.document.createElement('a')
        link.href = document.s3Url
        link.download = document.name
        link.target = '_blank'
        window.document.body.appendChild(link)
        link.click()
        window.document.body.removeChild(link)
        return
      }

      // New secure flow: ask backend for a short-lived URL
      if (!document.id) {
        console.error('❌ Cannot download document without ID:', document)
        alert('Document identifier missing; cannot download document')
        return
      }

      try {
        console.log('⬇️ Requesting secure download URL for document:', document.id, document.name)
        const response = await axiosInstance.get(
          API_ENDPOINTS.DOCUMENTS_DOWNLOAD(document.id),
          { params: { disposition: 'attachment' } }
        )

        if (response.data && response.data.success && response.data.downloadUrl) {
          const downloadUrl = response.data.downloadUrl
          console.log('⬇️ Downloading document from secure URL:', downloadUrl)

          const link = window.document.createElement('a')
          link.href = downloadUrl
          link.download = document.name
          link.target = '_blank'
          window.document.body.appendChild(link)
          link.click()
          window.document.body.removeChild(link)
        } else {
          console.error('❌ Failed to get secure download URL for document:', document, response.data)
          alert('Document URL not available for download')
        }
      } catch (err) {
        console.error('❌ Error getting secure download URL for document:', document, err)
        alert('Error while downloading document. Please try again.')
      }
    }

    const showDocumentDetails = (document) => {
      selectedDocument.value = document
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      selectedDocument.value = null
    }

    // Upload Methods
    const triggerFileInput = () => {
      fileInput.value.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        uploadMessage.value = ''
        console.log('📄 File selected:', file.name, file.size, file.type)
      }
    }

    const uploadDocument = async () => {
      if (!selectedFile.value || !uploadModule.value) {
        uploadMessage.value = 'Please select a file and module'
        uploadMessageType.value = 'error'
        return
      }

      try {
        uploading.value = true
        uploadProgress.value = 0
        uploadMessage.value = ''

        // Get user info from localStorage
        const userId = localStorage.getItem('user_name') || 'unknown-user'

        // Create FormData
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        formData.append('module', uploadModule.value)
        formData.append('framework', uploadFramework.value || '')
        formData.append('company', uploadCompany.value || '')
        formData.append('subfolder', uploadSubfolder.value || '')
        formData.append('user_id', userId)

        console.log('📤 Uploading document...')
        console.log('   File:', selectedFile.value.name)
        console.log('   Module:', uploadModule.value)
        console.log('   Framework:', uploadFramework.value || 'None')
        console.log('   User:', userId)

        // Use documentService for upload (automatically refreshes cache)
        const response = await documentDataService.uploadDocument(formData, (progress) => {
          uploadProgress.value = progress
        })

        if (response.data.success) {
          uploadMessage.value = `✅ Document uploaded successfully! ${response.data.stored_name || ''}`
          uploadMessageType.value = 'success'
          
          // Reset form
          selectedFile.value = null
          uploadModule.value = ''
          uploadFramework.value = ''
          uploadCompany.value = ''
          uploadSubfolder.value = ''
          uploadCompanySubfolders.value = []
          fileInput.value.value = ''
          uploadProgress.value = 0

          // Refresh documents list with pagination
          await fetchDocuments(currentPage.value)
          // Also refresh counts
          await fetchDocumentCounts()

          setTimeout(() => {
            uploadMessage.value = ''
          }, 3000)

          console.log('✅ Upload successful:', response.data)
        } else {
          uploadMessage.value = `❌ Upload failed: ${response.data.error || 'Unknown error'}`
          uploadMessageType.value = 'error'
          console.error('❌ Upload failed:', response.data)
        }

      } catch (err) {
        uploadMessage.value = `❌ Upload error: ${err.response?.data?.error || err.message}`
        uploadMessageType.value = 'error'
        console.error('❌ Upload error:', err)
      } finally {
        uploading.value = false
      }
    }

    const createCompanyFolder = async () => {
      if (!newCompanyName.value) {
        companyMessage.value = 'Please enter a company folder name'
        companyMessageType.value = 'error'
        return
      }

      try {
        creatingCompanyFolder.value = true
        companyMessage.value = ''

        const payload = {
          name: newCompanyName.value,
          description: newCompanyDescription.value
        }

        const response = await axiosInstance.post(API_ENDPOINTS.COMPANY_FOLDERS_CREATE, payload)

        if (response.data && response.data.success) {
          companyMessage.value = 'Company folder created successfully'
          companyMessageType.value = 'success'
          newCompanyName.value = ''
          newCompanyDescription.value = ''
          await loadCompanyFolders()
        } else {
          companyMessage.value = response.data.error || 'Failed to create company folder'
          companyMessageType.value = 'error'
        }
      } catch (err) {
        console.error('[DocumentHandling] ❌ Error creating company folder:', err)
        companyMessage.value = err.response?.data?.error || err.message || 'Failed to create company folder'
        companyMessageType.value = 'error'
      } finally {
        creatingCompanyFolder.value = false
        if (companyMessageType.value === 'success') {
          setTimeout(() => {
            companyMessage.value = ''
          }, 3000)
        }
      }
    }

    const createCompanySubfolder = async () => {
      if (!newSubfolderName.value || !selectedCompanyId.value) {
        subfolderMessage.value = 'Select a company and enter a folder name'
        subfolderMessageType.value = 'error'
        return
      }
      try {
        creatingSubfolder.value = true
        subfolderMessage.value = ''
        const response = await axiosInstance.post(
          API_ENDPOINTS.COMPANY_SUBFOLDERS_CREATE(selectedCompanyId.value),
          { name: newSubfolderName.value }
        )
        if (response.data && response.data.success) {
          subfolderMessage.value = 'Folder created'
          subfolderMessageType.value = 'success'
          newSubfolderName.value = ''
          await loadCompanySubfolders(selectedCompanyId.value)
          await loadCompanyFolders()
        } else {
          subfolderMessage.value = response.data.error || 'Failed to create folder'
          subfolderMessageType.value = 'error'
        }
      } catch (err) {
        subfolderMessage.value = err.response?.data?.error || err.message || 'Failed to create folder'
        subfolderMessageType.value = 'error'
      } finally {
        creatingSubfolder.value = false
        if (subfolderMessageType.value === 'success') {
          setTimeout(() => { subfolderMessage.value = '' }, 3000)
        }
      }
    }

    const confirmDeleteCompanyFolder = (company) => {
      if (!window.confirm(`Delete company folder "${company.name}"? This will also remove all subfolders and their document links. Files in S3 are not deleted.`)) return
      deleteCompanyFolder(company.id)
    }
    const deleteCompanyFolder = async (folderId) => {
      try {
        deletingFolderId.value = folderId
        const response = await axiosInstance.delete(API_ENDPOINTS.COMPANY_FOLDER_DELETE(folderId))
        if (response.data && response.data.success) {
          companyMessage.value = 'Company folder deleted'
          companyMessageType.value = 'success'
          if (selectedCompanyId.value === folderId) {
            selectedCompanyId.value = null
            selectedCompanyForDocs.value = ''
            activeCompanyCode.value = ''
            companySubfolders.value = []
            documents.value = []
          }
          await loadCompanyFolders()
        } else {
          companyMessage.value = response.data?.error || 'Failed to delete folder'
          companyMessageType.value = 'error'
        }
      } catch (err) {
        companyMessage.value = err.response?.data?.error || err.message || 'Failed to delete folder'
        companyMessageType.value = 'error'
      } finally {
        deletingFolderId.value = null
        setTimeout(() => { companyMessage.value = '' }, 3000)
      }
    }

    const confirmDeleteCompanySubfolder = (sub) => {
      if (!window.confirm(`Delete subfolder "${sub.name}"? Document links for this folder will be removed. Files are not deleted.`)) return
      deleteCompanySubfolder(sub)
    }
    const deleteCompanySubfolder = async (sub) => {
      if (!selectedCompanyId.value || !sub) return
      const subfolderId = sub.id
      try {
        deletingSubfolderId.value = subfolderId
        const response = await axiosInstance.delete(API_ENDPOINTS.COMPANY_SUBFOLDER_DELETE(selectedCompanyId.value, subfolderId))
        if (response.data && response.data.success) {
          subfolderMessage.value = 'Subfolder deleted'
          subfolderMessageType.value = 'success'
          if (selectedSubfolderCode.value === sub.code) {
            selectedSubfolderCode.value = ''
          }
          await loadCompanySubfolders(selectedCompanyId.value)
          await loadCompanyFolders()
          await loadCompanyDocuments()
        } else {
          subfolderMessage.value = response.data?.error || 'Failed to delete subfolder'
          subfolderMessageType.value = 'error'
        }
      } catch (err) {
        subfolderMessage.value = err.response?.data?.error || err.message || 'Failed to delete subfolder'
        subfolderMessageType.value = 'error'
      } finally {
        deletingSubfolderId.value = null
        setTimeout(() => { subfolderMessage.value = '' }, 3000)
      }
    }

    const confirmDeleteDocument = (document) => {
      if (!window.confirm(`Delete document "${document.name}"? This cannot be undone. The file will be removed from the list.`)) return
      deleteDocument(document.id)
    }
    const deleteDocument = async (docId) => {
      try {
        deletingDocId.value = docId
        const response = await axiosInstance.delete(API_ENDPOINTS.DOCUMENT_DELETE(docId))
        if (response.data && response.data.success) {
          documents.value = documents.value.filter(d => d.id !== docId)
          await loadCompanyFolders()
          if (selectedCompanyId.value) {
            await loadCompanySubfolders(selectedCompanyId.value)
            await loadCompanyDocuments()
          }
        } else {
          companyMessage.value = response.data?.error || 'Failed to delete document'
          companyMessageType.value = 'error'
          setTimeout(() => { companyMessage.value = '' }, 3000)
        }
      } catch (err) {
        companyMessage.value = err.response?.data?.error || err.message || 'Failed to delete document'
        companyMessageType.value = 'error'
        setTimeout(() => { companyMessage.value = '' }, 3000)
      } finally {
        deletingDocId.value = null
      }
    }

    return {
      activeModule,
      searchQuery,
      selectedFilter,
      showModal,
      selectedDocument,
      modules,
      documents,
      filteredDocuments,
      loading,
      error,
      documentCounts,
      getDocumentCount,
      getActiveModuleName,
      getFileIcon,
      formatDate,
      openDocument,
      downloadDocument,
      showDocumentDetails,
      closeModal,
      fetchDocuments,
      fetchDocumentCounts,
      // Pagination
      currentPage,
      pageSize,
      totalPages,
      totalCount,
      goToPage,
      nextPage,
      prevPage,
      getVisiblePages,
      // Upload
      selectedFile,
      uploadModule,
      uploadFramework,
      uploading,
      uploadProgress,
      uploadMessage,
      uploadMessageType,
      fileInput,
      triggerFileInput,
      handleFileSelect,
      uploadDocument,
      isBackgroundFetching,
      frameworks,
      loadFrameworks,
      // Company folders
      companyFolders,
      uploadCompany,
      uploadSubfolder,
      uploadCompanySubfolders,
      loadCompanyFolders,
      newCompanyName,
      newCompanyDescription,
      creatingCompanyFolder,
      companyMessage,
      companyMessageType,
      createCompanyFolder,
      activeCompanyCode,
      selectedCompanyForDocs,
      selectedCompanyId,
      loadCompanyDocuments,
      // Company subfolders (folders inside a company)
      companySubfolders,
      selectedSubfolderCode,
      newSubfolderName,
      creatingSubfolder,
      subfolderMessage,
      subfolderMessageType,
      createCompanySubfolder,
      loadCompanySubfolders,
      selectedCompanyName,
      selectedSubfolderName,
      companyFolderDocCount,
      uploadCompanyName,
      uploadSubfolderName,
      syncUploadToSelectedFolder,
      deletingFolderId,
      deletingSubfolderId,
      deletingDocId,
      confirmDeleteCompanyFolder,
      confirmDeleteCompanySubfolder,
      confirmDeleteDocument
    }
  }
}
</script>