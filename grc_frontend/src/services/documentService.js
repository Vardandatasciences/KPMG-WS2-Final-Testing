/**
 * Document Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all document-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

const DEFAULT_DOCUMENT_COUNTS = () => ({
  all: 0,
  policy: 0,
  audit: 0,
  incident: 0,
  risk: 0,
  event: 0
});

const filterSyntheticDocuments = (documents = []) =>
  documents.filter((doc) => (doc.module || '').toLowerCase() !== 'synthetic');

class DocumentService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      documents: [],
      documentCounts: DEFAULT_DOCUMENT_COUNTS(),
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all document data and cache it
   */
  async fetchAllDocumentData() {
    // Check if user is authenticated before fetching
    const isAuthenticated = localStorage.getItem('is_logged_in') === 'true' && 
                           localStorage.getItem('access_token') !== null;
    
    if (!isAuthenticated) {
      console.warn('[Document Service] ⚠️ User not authenticated, cannot fetch documents');
      throw new Error('User must be authenticated to fetch documents');
    }

    if (this.dataStore.isFetching) {
      console.log('[Document Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Document Service] 🚀 Starting document data prefetch...');

    try {
      // Fetch all document-related datasets
      await Promise.all([
        this.fetchDocuments(),
        this.fetchDocumentCounts()
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Document Service] ✅ Prefetch complete - Total documents: ${this.dataStore.documents.length}`);
      console.log(`[Document Service] ✅ Document counts:`, this.dataStore.documentCounts);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Document Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch documents from API with pagination support
   */
  async fetchDocuments(params = {}) {
    try {
      const queryParams = {
        module: params.module || 'all',
        search: params.search || '',
        file_type: params.file_type || 'all',
        page: params.page || 1,
        page_size: params.page_size || 20
      };

      const response = await axiosInstance.get(API_ENDPOINTS.DOCUMENTS_LIST, {
        params: queryParams,
        timeout: 60000
      });

      if (response.data.success) {
        const paginatedDocs = filterSyntheticDocuments(response.data.documents);
        
        // If pagination is used, store pagination metadata
        if (params.page !== undefined) {
          this.dataStore.pagination = {
            page: response.data.page || params.page,
            page_size: response.data.page_size || params.page_size,
            total_count: response.data.total_count || 0,
            total_pages: response.data.total_pages || 0
          };
          // For paginated requests, replace documents instead of appending
          this.dataStore.documents = paginatedDocs;
        } else {
          // For non-paginated requests (backward compatibility)
          this.dataStore.documents = paginatedDocs;
        }
        
        console.log(`[Document Service] Fetched ${paginatedDocs.length} documents (page ${queryParams.page})`);
      } else {
        this.dataStore.documents = [];
      }
      
      return {
        documents: this.dataStore.documents,
        pagination: this.dataStore.pagination
      };
    } catch (error) {
      console.error('[Document Service] Error fetching documents:', error);
      this.dataStore.documents = [];
      throw error;
    }
  }

  /**
   * Fetch document counts from API
   */
  async fetchDocumentCounts() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.DOCUMENTS_COUNTS, {
        timeout: 60000
      });

      if (response.data.success) {
        this.dataStore.documentCounts = {
          ...DEFAULT_DOCUMENT_COUNTS(),
          ...(response.data.counts || {})
        };
        console.log(`[Document Service] Fetched document counts:`, this.dataStore.documentCounts);
      } else {
        this.dataStore.documentCounts = DEFAULT_DOCUMENT_COUNTS();
      }
    } catch (error) {
      console.error('[Document Service] Error fetching document counts:', error);
      this.dataStore.documentCounts = DEFAULT_DOCUMENT_COUNTS();
      throw error;
    }
  }

  /**
   * Upload a new document
   * @param {FormData} formData - The form data containing the file and metadata
   * @param {Function} onProgress - Callback for upload progress
   * @returns {Promise} Upload response
   */
  async uploadDocument(formData, onProgress) {
    try {
      console.log('[Document Service] Uploading document...');
      
      const response = await axiosInstance.post(API_ENDPOINTS.DOCUMENTS_UPLOAD, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentCompleted);
          }
        },
        timeout: 120000 // 2 minutes for large files
      });

      if (response.data.success) {
        console.log('[Document Service] ✅ Document uploaded successfully');
        // Refresh documents and counts after successful upload
        await this.fetchDocuments();
        await this.fetchDocumentCounts();
      }

      return response;
    } catch (error) {
      console.error('[Document Service] ❌ Error uploading document:', error);
      throw error;
    }
  }

  /**
   * Get cached data
   * @param {string} key - The data key to retrieve
   * @returns {any} The cached data
   */
  getData(key) {
    return this.dataStore[key];
  }

  /**
   * Set cached data
   * @param {string} key - The data key to set
   * @param {any} value - The value to set
   */
  setData(key, value) {
    if (Object.prototype.hasOwnProperty.call(this.dataStore, key)) {
      let sanitizedValue = value;
      if (key === 'documents') {
        sanitizedValue = filterSyntheticDocuments(value || []);
      } else if (key === 'documentCounts') {
        sanitizedValue = {
          ...DEFAULT_DOCUMENT_COUNTS(),
          ...(value || {})
        };
      }

      this.dataStore[key] = sanitizedValue;
      if (key !== 'lastFetchTime' && key !== 'isFetching' && key !== 'fetchError') {
        this.dataStore.lastFetchTime = new Date();
      }
    }
  }

  /**
   * Check if data is cached and fresh
   * @returns {boolean}
   */
  hasValidCache() {
    // Cache is valid if data was fetched (even if empty) OR if we have documents
    const hasCache = this.dataStore.lastFetchTime !== null || this.dataStore.documents.length > 0;
    console.log('[Document Service] hasValidCache check:', {
      lastFetchTime: this.dataStore.lastFetchTime,
      documentsCount: this.dataStore.documents.length,
      hasCache: hasCache
    });
    return hasCache;
  }

  /**
   * Filter documents by module
   * @param {string} module - The module to filter by
   * @returns {Array} Filtered documents
   */
  getDocumentsByModule(module) {
    if (module === 'all') {
      return this.dataStore.documents;
    }
    return this.dataStore.documents.filter(doc => doc.module.toLowerCase() === module.toLowerCase());
  }

  /**
   * Search documents by query
   * @param {string} query - The search query
   * @returns {Array} Filtered documents
   */
  searchDocuments(query) {
    if (!query) {
      return this.dataStore.documents;
    }
    const lowerQuery = query.toLowerCase();
    return this.dataStore.documents.filter(doc => 
      doc.name.toLowerCase().includes(lowerQuery) ||
      doc.uploadedBy.toLowerCase().includes(lowerQuery) ||
      doc.module.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.documents = [];
    this.dataStore.documentCounts = DEFAULT_DOCUMENT_COUNTS();
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Document Service] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      documentsCount: this.dataStore.documents.length,
      documentCounts: this.dataStore.documentCounts,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const documentDataService = new DocumentService();
export default documentDataService;

