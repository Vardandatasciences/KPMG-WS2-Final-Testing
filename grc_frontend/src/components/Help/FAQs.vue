<template>
  <div class="help-page">
    <div class="help-container">
      <!-- Header -->
      <div class="help-header">
        <h1 class="help-title">
          <i class="fas fa-question-circle"></i>
          Frequently Asked Questions
        </h1>
        <p class="help-subtitle">
          Find answers to common questions about RiskaVaire platform usage, troubleshooting, and best practices.
        </p>
      </div>
      
      <!-- Download Button - Moved down and to the left -->
      <div class="content-section">
        <div class="download-section">
          <button class="btn btn-submit download-button" @click="downloadPDF">
            <i class="fas fa-eye"></i>
            View PDF
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const downloadPDF = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire FAQs.pdf';
  window.open(pdfUrl, '_blank', 'noopener,noreferrer');
};
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background: white;
  padding: 0.5rem 2rem 2rem;
} 

.help-container {
  max-width: 1000px;
  padding-left: 30px;
  margin: 0 auto;
  background: white;
  overflow: hidden;
}

.help-header {
  background: white;
  color: #1f2937;
  padding: 1.5rem 2rem 1rem;
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
  line-height: 1.6;
  margin-left:40px;
  margin-bottom: 2rem;
}

.content-section {
  padding: 2rem;
}

.download-section {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 2rem;
}

/* Scoped styles to maintain button size while using global btn styles */
.download-button {
  padding: 0.5rem 1rem !important;
  font-size: 0.85rem !important;
  min-height: auto !important;
  height: auto !important;
  max-height: none !important;
  border-radius: 6px !important;
  margin-left: 40px !important;
  gap: 0.4rem !important;
}

.download-button i {
  font-size: 0.9rem;
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

  .download-button {
    width: 100%;
    max-width: 300px;
  }
  
  .help-title {
    font-size: 2rem;
  }
}
</style>
