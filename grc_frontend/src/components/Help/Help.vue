<template>
  <div class="help-container">
    <div class="help-navigation">
      <div class="toggle-group">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['toggle-button', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon"></i>
          {{ tab.label }}
        </button>
      </div>
    </div>
    <div class="tab-content">
      <!-- Contact Us Tab -->
      <div v-if="activeTab === 'contact'" class="help-section">
        <h2 class="section-title">
          <i class="fas fa-phone-alt section-icon-base"></i>
          Contact Us
        </h2>
        <p class="section-helper">For more information and guidance please contact us</p>
        
        <div class="contact-content">
          <div class="contact-grid">
            <!-- Left Column - Contact Information -->
            <div class="contact-info-section">
              <div class="contact-item">
                <div class="contact-icon-base contact-icon">
                  <i class="fas fa-envelope"></i>
                </div>
                <div class="contact-details">
                  <h3>Email</h3>
                  <p>info@vardaanglobal.com</p>
                </div>
              </div>
              
              <div class="contact-item">
                <div class="contact-icon-base contact-icon">
                  <i class="fas fa-phone"></i>
                </div>
                <div class="contact-details">
                  <h3>Phone</h3>
                  <p>+91 40-35171118</p>
                  <p>+91 40-35171119</p>
                </div>
              </div>
              
              <div class="contact-item">
                <div class="contact-icon-base contact-icon">
                  <i class="fas fa-globe"></i>
                </div>
                <div class="contact-details">
                  <h3>Website</h3>
                  <p>https://vardaands.com</p>
                </div>
              </div>
            </div>

            <!-- Right Column - Address -->
            <div class="address-section">
              <div class="contact-item">
                <div class="contact-icon-base contact-icon">
                  <i class="fas fa-map-marker-alt"></i>
                </div>
                <div class="contact-details">
                  <h3>Address</h3>
                  <p>Aurum, 1st Floor, Plot No 57,</p>
                  <p>Jayabheri Enclave,</p>
                  <p>Gachibowli, Hyderabad - 500032,</p>
                  <p>INDIA</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- FAQs Tab -->
      <div v-if="activeTab === 'faqs'" class="help-section">
        <h2 class="section-title">
          <i class="fas fa-question-circle section-icon-base"></i>
          Frequently Asked Questions
        </h2>
        <p class="section-helper">Find answers to common questions about RiskaVaire platform usage, troubleshooting, and best practices.</p>
        
        <div class="content-section">
          <div class="download-section">
            <button class="btn btn-submit download-button" @click="downloadFAQs">
              <i class="fas fa-eye"></i>
              View PDF
            </button>
          </div>
        </div>
      </div>

      <!-- User Manual Tab -->
      <div v-if="activeTab === 'manual'" class="help-section">
        <h2 class="section-title">
          <i class="fas fa-book section-icon-base"></i>
          User Manual
        </h2>
        <p class="section-helper">Comprehensive guide to using RiskaVaire platform features, workflows, and best practices for effective GRC management.</p>
        
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

      <!-- Privacy & Security Tab -->
      <div v-if="activeTab === 'privacy'" class="help-section">
        <h2 class="section-title">
          <i class="fas fa-shield-alt section-icon-base"></i>
          Privacy & Security
        </h2>
        <p class="section-helper">Learn about our data privacy practices, security measures, and how we protect your information in the RiskaVaire platform.</p>
        
        <div class="privacy-security-content-section">
          <div class="download-section">
            <button class="btn btn-submit download-button" @click="downloadPrivacyPDF">
              <i class="fas fa-eye"></i>
              View Document
            </button>
          </div>
        </div>

        <div class="privacy-security-content">
          <!-- Security Best Practices -->
          <section class="privacy-security-section">
            <h2 class="privacy-security-section-title">
              <i class="fas fa-user-secret"></i>
              Security Best Practices
            </h2>
            <div class="best-practices">
              <div class="practice-card">
                <h3>For Users</h3>
                <div class="practice-list">
                  <div class="practice-item">
                    <i class="fas fa-key"></i>
                    <div>
                      <h4>Strong Passwords</h4>
                      <p>Use complex passwords with a mix of letters, numbers, and special characters. Change passwords regularly.</p>
                    </div>
                  </div>
                  <div class="practice-item">
                    <i class="fas fa-mobile-alt"></i>
                    <div>
                      <h4>Enable MFA</h4>
                      <p>Always enable multi-factor authentication for additional security protection.</p>
                    </div>
                  </div>
                  <div class="practice-item">
                    <i class="fas fa-sign-out-alt"></i>
                    <div>
                      <h4>Secure Logout</h4>
                      <p>Always log out when finished, especially on shared or public computers.</p>
                    </div>
                  </div>
                  <div class="practice-item">
                    <i class="fas fa-eye-slash"></i>
                    <div>
                      <h4>Be Aware</h4>
                      <p>Never share your credentials and be cautious of phishing attempts.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="practice-card">
                <h3>For Administrators</h3>
                <div class="practice-list">
                  <div class="practice-item">
                    <i class="fas fa-users-cog"></i>
                    <div>
                      <h4>User Management</h4>
                      <p>Regularly review and update user access permissions. Remove access for inactive users.</p>
                    </div>
                  </div>
                  <div class="practice-item">
                    <i class="fas fa-chart-line"></i>
                    <div>
                      <h4>Monitor Activity</h4>
                      <p>Regularly review audit logs and system activity for suspicious behavior.</p>
                    </div>
                  </div>
                  <div class="practice-item">
                    <i class="fas fa-download"></i>
                    <div>
                      <h4>Regular Backups</h4>
                      <p>Ensure regular backups are performed and test recovery procedures.</p>
                    </div>
                  </div>
                  <div class="practice-item">
                    <i class="fas fa-graduation-cap"></i>
                    <div>
                      <h4>Security Training</h4>
                      <p>Provide regular security awareness training to all users.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Contact Security Team -->
          <section class="privacy-security-section">
            <div class="security-contact">
              <h2>Security Concerns?</h2>
              <p>If you have security concerns or suspect a security incident, contact our security team immediately.</p>
              <div class="contact-boxes">
                <div class="contact-box">
                  <i class="fas fa-envelope"></i>
                  <h4>Email</h4>
                  <p>info@vardaanglobal.com</p>
                </div>
                <div class="contact-box">
                  <i class="fas fa-phone"></i>
                  <h4>Phone 1</h4>
                  <p>+91 40-35171118</p>
                </div>
                <div class="contact-box">
                  <i class="fas fa-phone"></i>
                  <h4>Phone 2</h4>
                  <p>+91 40-35171119</p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <!-- Feedback Tab -->
      <div v-if="activeTab === 'feedback'" class="help-section">
        <h2 class="section-title">
          <i class="fas fa-lightbulb section-icon-base"></i>
          Feedback
        </h2>
        <p class="section-helper">We value your input to make RiskaVaire more effective and user-friendly. Share your experience, report issues, or suggest new features.</p>
        
        <div class="feedback-content">
          <!-- Simple Feedback Section -->
          <div class="simple-feedback-section">
            <h2>Help Us Improve</h2>
            <p>
              We value your input to make RiskaVaire more effective and user-friendly. Use the feedback form to share your experience, report issues, or suggest new features. Your feedback will be reviewed by our product team and, where relevant, integrated into our roadmap.
            </p>
            <div class="feedback-button-container">
              <button class="btn btn-submit feedback-button" @click="openFeedbackForm">
                <i class="fas fa-comment-alt"></i>
                Share Feedback
              </button>
            </div>
          </div>

          <div class="feedback-section">
            <div class="feedback-info">
              <h3>What Happens Next?</h3>
              <div class="info-grid">
                <div class="info-item">
                  <i class="fas fa-eye"></i>
                  <h4>Review</h4>
                  <p>Our team reviews all feedback within 48 hours</p>
                </div>
                <div class="info-item">
                  <i class="fas fa-reply"></i>
                  <h4>Response</h4>
                  <p>We'll acknowledge your feedback and provide updates</p>
                </div>
                <div class="info-item">
                  <i class="fas fa-road"></i>
                  <h4>Roadmap</h4>
                  <p>Valuable suggestions are considered for future releases</p>
                </div>
                <div class="info-item">
                  <i class="fas fa-check-circle"></i>
                  <h4>Implementation</h4>
                  <p>Approved features are developed and released</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Acknowledgement Tab -->
      <div v-if="activeTab === 'acknowledgement'" class="help-section">
        <h2 class="section-title">
          <i class="fas fa-handshake section-icon-base"></i>
          Acknowledgement
        </h2>
        <p class="section-helper">We extend our gratitude to all contributors, partners, and stakeholders who have supported the development and success of the RiskaVaire platform.</p>
        
        <div class="ack-content">
          <!-- Open Source Attribution -->
          <section class="ack-section">
            <div class="pdf-section">
              <h2 class="ack-section-title">
                <i class="fas fa-file-pdf"></i>
                Open Source Attribution
              </h2>
              <p class="pdf-description">
                This document contains detailed information about the open-source libraries, frameworks, and tools used in the development of RiskaVaire, along with their respective licenses and attributions.
              </p>
              <div class="pdf-button-container">
                <button class="btn btn-submit view-pdf-button" @click="openPDF">
                  <i class="fas fa-eye"></i>
                  View PDF
                </button>
              </div>
            </div>
          </section>

          <!-- Development Team -->
          <section class="ack-section">
            <h2 class="ack-section-title">
              <i class="fas fa-users"></i>
              Development Team
            </h2>
            <div class="acknowledgement-grid">
              <div class="acknowledgement-card">
                <h3>Core Development</h3>
                <div class="team-list">
                  <div class="team-member">
                    <i class="fas fa-code"></i>
                    <div>
                      <h4>Software Engineers</h4>
                      <p>Our dedicated team of developers who built the robust foundation of RiskaVaire with cutting-edge technologies and best practices.</p>
                    </div>
                  </div>
                  <div class="team-member">
                    <i class="fas fa-palette"></i>
                    <div>
                      <h4>UI/UX Designers</h4>
                      <p>Creative professionals who crafted the intuitive and user-friendly interface that makes GRC management accessible to all users.</p>
                    </div>
                  </div>
                  <div class="team-member">
                    <i class="fas fa-database"></i>
                    <div>
                      <h4>Data Architects</h4>
                      <p>Experts who designed the scalable and secure data infrastructure that powers our comprehensive GRC solutions.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="acknowledgement-card">
                <h3>Quality Assurance</h3>
                <div class="team-list">
                  <div class="team-member">
                    <i class="fas fa-bug"></i>
                    <div>
                      <h4>QA Engineers</h4>
                      <p>Diligent testers who ensure the platform meets the highest standards of reliability, security, and performance.</p>
                    </div>
                  </div>
                  <div class="team-member">
                    <i class="fas fa-shield-alt"></i>
                    <div>
                      <h4>Security Specialists</h4>
                      <p>Cybersecurity experts who implemented robust security measures to protect sensitive GRC data and user information.</p>
                    </div>
                  </div>
                  <div class="team-member">
                    <i class="fas fa-tachometer-alt"></i>
                    <div>
                      <h4>Performance Engineers</h4>
                      <p>Specialists who optimized the platform for speed, efficiency, and seamless user experience across all devices.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Business Partners -->
          <section class="ack-section">
            <h2 class="ack-section-title">
              <i class="fas fa-handshake"></i>
              Business Partners
            </h2>
            <div class="partners-grid">
              <div class="partner-card">
                <i class="fas fa-building"></i>
                <h3>Vardaan Data Sciences</h3>
                <p>Our parent company and strategic partner who provided the vision, resources, and expertise to bring RiskaVaire to life.</p>
              </div>
              <div class="partner-card">
                <i class="fas fa-graduation-cap"></i>
                <h3>Academic Institutions</h3>
                <p>Universities and research institutions that contributed valuable insights and validation to our GRC methodologies.</p>
              </div>
              <div class="partner-card">
                <i class="fas fa-industry"></i>
                <h3>Industry Experts</h3>
                <p>GRC professionals and consultants who shared their domain expertise and real-world experience to shape our platform.</p>
              </div>
            </div>
          </section>

          <!-- Technology Stack -->
          <section class="ack-section">
            <h2 class="ack-section-title">
              <i class="fas fa-cogs"></i>
              Technology Stack
            </h2>
            <div class="tech-grid">
              <div class="tech-category">
                <h3>Frontend Technologies</h3>
                <div class="tech-list">
                  <div class="tech-item">
                    <i class="fab fa-vuejs"></i>
                    <span>Vue.js</span>
                  </div>
                  <div class="tech-item">
                    <i class="fab fa-js"></i>
                    <span>JavaScript</span>
                  </div>
                  <div class="tech-item">
                    <i class="fab fa-css3-alt"></i>
                    <span>CSS3</span>
                  </div>
                  <div class="tech-item">
                    <i class="fab fa-html5"></i>
                    <span>HTML5</span>
                  </div>
                </div>
              </div>
              <div class="tech-category">
                <h3>Backend Technologies</h3>
                <div class="tech-list">
                  <div class="tech-item">
                    <i class="fab fa-python"></i>
                    <span>Python</span>
                  </div>
                  <div class="tech-item">
                    <i class="fab fa-node-js"></i>
                    <span>Django</span>
                  </div>
                  <div class="tech-item">
                    <i class="fas fa-database"></i>
                    <span>PostgreSQL</span>
                  </div>
                  <div class="tech-item">
                    <i class="fab fa-aws"></i>
                    <span>AWS</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Special Thanks -->
          <section class="ack-section">
            <div class="special-thanks">
              <h2>Special Thanks</h2>
              <p>We would like to express our deepest gratitude to all our beta testers, early adopters, and customers who provided invaluable feedback and helped us refine RiskaVaire into the powerful GRC platform it is today.</p>
              <div class="thanks-highlight">
                <i class="fas fa-heart"></i>
                <p>Your trust and support drive us to continuously improve and innovate.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

// Define component name to satisfy vue/multi-word-component-names rule
defineOptions({
  name: 'HelpPage'
})

const route = useRoute()
const activeTab = ref('contact')

const tabs = [
  { key: 'contact', label: 'Contact Us', icon: 'fas fa-phone-alt' },
  { key: 'faqs', label: 'FAQs', icon: 'fas fa-question-circle' },
  { key: 'manual', label: 'User Manual', icon: 'fas fa-book' },
  { key: 'privacy', label: 'Privacy & Security', icon: 'fas fa-shield-alt' },
  { key: 'feedback', label: 'Feedback', icon: 'fas fa-lightbulb' },
  { key: 'acknowledgement', label: 'Acknowledgement', icon: 'fas fa-handshake' }
]

// Set initial tab based on route query or hash
onMounted(() => {
  const tabParam = route.query.tab || route.hash.replace('#', '')
  if (tabParam && tabs.find(t => t.key === tabParam)) {
    activeTab.value = tabParam
  }
})

// PDF download functions
const downloadFAQs = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire FAQs.pdf'
  window.open(pdfUrl, '_blank', 'noopener,noreferrer')
}

const downloadAdminManual = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire Admin User Manual.pdf'
  window.open(pdfUrl, '_blank', 'noopener,noreferrer')
}

const downloadNonAdminManual = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire Non-admin user manual.pdf'
  window.open(pdfUrl, '_blank', 'noopener,noreferrer')
}

const downloadPrivacyPDF = () => {
  const pdfUrl = '/assets/help_docs/Privacy and Security Policy1.pdf'
  window.open(pdfUrl, '_blank', 'noopener,noreferrer')
}

const openFeedbackForm = () => {
  window.open('https://forms.office.com/r/wGG9gwkkXN', '_blank', 'noopener,noreferrer')
}

const openPDF = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire Open-Source Attribution.pdf'
  window.open(pdfUrl, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
@import '../Login/UserProfile.css';

.help-container {
  max-width: calc(100% - 240px);
  width: calc(100% - 240px);
  margin: 0 0 0 240px;
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: white;
  min-height: 100vh;
}

.help-navigation {
  margin-bottom: 2rem;
  display: flex;
  width: 100%;
  border: none !important;
  border-bottom: none !important;
}

.help-navigation .toggle-group {
  margin: 0;
  width: 100%;
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  border: none !important;
  border-bottom: none !important;
}

.help-navigation .toggle-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: none !important;
}

/* Hide the ::after line only for inactive buttons, keep it for active */
.help-navigation .toggle-button:not(.active)::after {
  display: none !important;
}

.help-navigation .toggle-button.active::after {
  display: block !important;
}

.help-navigation .toggle-button i {
  font-size: 18px;
  margin-right: 0;
}

.tab-content {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
  animation: fadeInUp 0.6s ease-out;
  width: 100%;
  border: none !important;
  border-top: none !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}

.help-section {
  padding: 2rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.section-helper {
  color: #64748b;
  margin-bottom: 2rem;
  margin-left: 24px; /* Align with heading text (icon width ~24px + gap 12px) */
  line-height: 1.6;
  text-align: left !important;
}

/* Contact Us Styles */
.contact-content {
  padding: 0;
}

.contact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: start;
}

.contact-info-section,
.address-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.contact-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: transform 0.2s, box-shadow 0.2s;
}

.contact-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.contact-details {
  flex: 1;
}

.contact-details h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.contact-details p {
  font-size: 0.9rem;
  color: #4b5563;
  margin-bottom: 0.25rem;
  line-height: 1.5;
}

.contact-details p:last-child {
  margin-bottom: 0;
}

/* FAQs Styles */
.content-section {
  padding: 0;
}

.download-section {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 2rem;
}

.download-button {
  padding: 0.5rem 1rem !important;
  font-size: 0.85rem !important;
  min-height: auto !important;
  height: auto !important;
  max-height: none !important;
  border-radius: 6px !important;
  gap: 0.4rem !important;
}

/* User Manual Styles */
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

/* Privacy & Security Styles */
.privacy-security-content-section {
  padding: 0 0 2rem 0;
}

.privacy-security-content {
  padding: 0;
}

.privacy-security-section {
  margin-bottom: 3rem;
}

.privacy-security-section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 40px;
  color: #1f2937;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.best-practices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.practice-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.practice-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.practice-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.practice-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.practice-item i {
  color: #3b82f6;
  font-size: 1.25rem;
  margin-top: 0.125rem;
}

.practice-item h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.practice-item p {
  color: #6b7280;
  line-height: 1.5;
}

.security-contact {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.security-contact h2 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.security-contact p {
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.contact-boxes {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-top: 2rem;
}

.contact-box {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  text-align: center;
  min-width: 200px;
  max-width: 250px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.contact-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.contact-box i {
  color: #3b82f6;
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.contact-box h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.contact-box p {
  color: #6b7280;
  font-size: 0.8rem;
  margin: 0;
  word-break: break-word;
}

/* Feedback Styles */
.feedback-content {
  padding: 0;
}

.simple-feedback-section {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 3rem;
}

.simple-feedback-section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.simple-feedback-section p {
  font-size: 0.9rem;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.feedback-button-container {
  display: flex;
  justify-content: center;
}

.feedback-button {
  padding: 0.6rem 1.1rem !important;
  font-size: 0.9rem !important;
  min-height: auto !important;
  height: auto !important;
  max-height: none !important;
  border-radius: 8px !important;
  gap: 0.4rem !important;
}

.feedback-section {
  max-width: 1000px;
  margin: 0 auto;
}

.feedback-info {
  margin-top: 3rem;
}

.feedback-info h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  text-align: center;
  margin-bottom: 2rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  text-align: center;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.info-item i {
  font-size: 2rem;
  color: #3b82f6;
  margin-bottom: 1rem;
}

.info-item h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.info-item p {
  color: #6b7280;
  line-height: 1.5;
  font-size: 0.8rem;
}

/* Acknowledgement Styles */
.ack-content {
  padding: 0;
}

.ack-section {
  margin-bottom: 3rem;
}

.ack-section-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pdf-section {
  margin-top: 2rem;
  text-align: center;
}

.pdf-description {
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.pdf-button-container {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.view-pdf-button {
  padding: 0.6rem 1.1rem !important;
  font-size: 0.9rem !important;
  min-height: auto !important;
  height: auto !important;
  max-height: none !important;
  border-radius: 8px !important;
  gap: 0.4rem !important;
}

.acknowledgement-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.acknowledgement-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.acknowledgement-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.team-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.team-member {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.team-member i {
  color: #3b82f6;
  font-size: 1.25rem;
  margin-top: 0.125rem;
}

.team-member h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.team-member p {
  color: #6b7280;
  line-height: 1.5;
}

.partners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.partner-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.partner-card i {
  color: #3b82f6;
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.partner-card h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.partner-card p {
  color: #6b7280;
  line-height: 1.5;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.tech-category {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.tech-category h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
  text-align: center;
}

.tech-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.tech-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  transition: transform 0.2s;
}

.tech-item:hover {
  transform: translateY(-2px);
}

.tech-item i {
  font-size: 2rem;
  color: #3b82f6;
}

.tech-item span {
  font-size: 0.8rem;
  font-weight: 500;
  color: #374151;
}

.special-thanks {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.special-thanks h2 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.special-thanks p {
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.thanks-highlight {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.thanks-highlight i {
  color: #ef4444;
  font-size: 1.5rem;
}

.thanks-highlight p {
  color: #374151;
  font-weight: 500;
  margin: 0;
}

/* Responsive Design */
@media (max-width: 768px) {
  .help-container {
    padding: 1rem;
    max-width: 100%;
    width: 100%;
    margin: 0;
  }
  
  .help-navigation .toggle-group {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .help-navigation .toggle-button {
    font-size: 0.9rem;
  }
  
  .contact-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .manual-options {
    flex-direction: column;
    gap: 1rem;
  }
  
  .manual-option {
    width: 100%;
    max-width: 300px;
  }
  
  .best-practices {
    grid-template-columns: 1fr;
  }
  
  .contact-boxes {
    flex-direction: column;
    align-items: center;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .acknowledgement-grid,
  .partners-grid,
  .tech-grid {
    grid-template-columns: 1fr;
  }
  
  .tech-list {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .thanks-highlight {
    flex-direction: column;
    text-align: center;
  }
}

/* Dark Theme Styles */
[data-theme="dark"] .help-navigation .toggle-button.active::after,
[data-theme="dark"] .help-navigation .toggle-button.is-active::after {
  background: #3b82f6 !important; /* Dark blue for dark theme */
}

[data-theme="dark"] .help-navigation .toggle-button:hover::after {
  background: rgba(59, 130, 246, 0.3) !important; /* Dark blue with opacity for hover */
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

