<template>
  <div class="help-page">
    <div class="help-container">
      <!-- Header -->
      <div class="help-header">
        <h1 class="help-title">
          <i class="fas fa-book"></i>
          User Manual
        </h1>
        <p class="help-subtitle">
          Comprehensive guide to using RiskaVaire platform features, workflows, and best practices for effective GRC management.
        </p>
      </div>
      
      <!-- Download Buttons - Two options for Admin and Non-admin -->
      <div class="content-section">
        <div class="download-section">
          <div class="manual-options">
            <div class="manual-option">
              <h3 class="manual-title">
                <i class="fas fa-user-shield"></i>
                Admin User Manual
              </h3>
              <p class="manual-description">
                Complete guide for administrators managing the RiskaVaire platform, including user management, system configuration, and advanced features.
              </p>
              <button class="btn btn-submit download-button admin-button" @click="downloadAdminManual">
                <i class="fas fa-eye"></i>
                View Admin Manual
              </button>
            </div>
            
            <div class="manual-option">
              <h3 class="manual-title">
                <i class="fas fa-user"></i>
                Non-Admin User Manual
              </h3>
              <p class="manual-description">
                User guide for regular users covering daily operations, policy management, compliance tracking, and basic platform features.
              </p>
              <button class="btn btn-submit download-button non-admin-button" @click="downloadNonAdminManual">
                <i class="fas fa-eye"></i>
                View Non-Admin Manual
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const downloadAdminManual = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire Admin User Manual.pdf';
  window.open(pdfUrl, '_blank');
};

const downloadNonAdminManual = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire Non-admin user manual.pdf';
  window.open(pdfUrl, '_blank');
};
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background: #ffffff;
  padding: 2rem;
}

.help-container {
  max-width: 1200px;
  margin: 0 auto;
  margin-left: 220px;
  margin-top: -30px;
  background: white;
  overflow: hidden;
}

.help-header {
  background: white;
  color: #1f2937;
  padding: 2rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}

.help-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 1rem;
}

.help-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-left: 40px;
  line-height: 1.6;
  margin-bottom: 0.6rem;
}

.content-section {
  padding: 2rem;
}

.download-section {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 2rem;
}

.manual-options {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  align-items: stretch;
}

.manual-option {
  flex: 1;
  min-width: 300px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1.5rem;
  text-align: left;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.manual-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.75rem;
}

.manual-description {
  font-size: 0.9rem;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  flex-grow: 1;
}

/* Buttons now use global styles from main.css */
/* Scoped overrides to maintain size and appearance */
.download-button {
  padding: 0.3rem 0.7rem !important;
  font-size: 0.8rem !important;
  border-radius: 6px !important;
  min-height: auto !important;
  height: auto !important;
  max-height: none !important;
  width: fit-content !important;
  gap: 0.5rem !important;
  justify-content: flex-start !important;
}

.admin-button {
  background-color: #10b981 !important;
  border-color: #10b981 !important;
}

.admin-button:hover:not(:disabled) {
  background-color: #059669 !important;
  border-color: #059669 !important;
}

.non-admin-button {
  background-color: #f59e0b !important;
  border-color: #f59e0b !important;
}

.non-admin-button:hover:not(:disabled) {
  background-color: #d97706 !important;
  border-color: #d97706 !important;
}

/* Colorblindness support for admin button - deuteranopia (green color blindness) */
[data-colorblind="deuteranopia"] .admin-button {
  background-color: #0f766e !important;
  border-color: #0f766e !important;
}

[data-colorblind="deuteranopia"] .admin-button:hover:not(:disabled) {
  background-color: #115e59 !important;
  border-color: #115e59 !important;
}

@media (max-width: 768px) {
  .help-page {
    padding: 1rem;
  }
  
  .help-header {
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .content-section {
    padding: 1rem;
  }

  .download-section {
    justify-content: center;
  }

  .manual-options {
    flex-direction: column;
    gap: 1rem;
  }

  .manual-option {
    width: 100%;
    max-width: 300px;
  }

  .download-button {
    width: 100%;
    max-width: 300px;
  }
  
  .help-title {
    font-size: 2rem;
  }
}
</style>
