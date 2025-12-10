<template>
  <div class="cookie-policy-page">
    <div class="cookie-policy-container">
      <div class="cookie-policy-header">
        <h1>Cookie Policy</h1>
        <p class="cookie-policy-last-updated">Last updated: {{ lastUpdated }}</p>
      </div>

      <div class="cookie-policy-content">
        <section class="cookie-policy-section">
          <h2>What Are Cookies?</h2>
          <p>
            Cookies are small text files that are placed on your computer or mobile device when you visit a website. 
            They are widely used to make websites work more efficiently and provide information to the website owners.
          </p>
        </section>

        <section class="cookie-policy-section">
          <h2>How We Use Cookies</h2>
          <p>
            We use cookies to enhance your experience on our website, analyze site traffic, and personalize content. 
            The information collected through cookies helps us understand how visitors interact with our website and 
            allows us to improve our services.
          </p>
        </section>

        <section class="cookie-policy-section">
          <h2>Types of Cookies We Use</h2>

          <div class="cookie-type-card">
            <div class="cookie-type-header">
              <h3>Essential Cookies</h3>
              <span class="cookie-badge cookie-badge-required">Required</span>
            </div>
            <p>
              These cookies are necessary for the website to function and cannot be switched off. They are usually 
              only set in response to actions made by you such as setting your privacy preferences, logging in, 
              or filling in forms. You can set your browser to block or alert you about these cookies, but some 
              parts of the site will not work if you do so.
            </p>
            <p class="cookie-examples">
              <strong>Examples:</strong> Session management, authentication, security features
            </p>
          </div>

          <div class="cookie-type-card">
            <div class="cookie-type-header">
              <h3>Functional Cookies</h3>
              <span class="cookie-badge cookie-badge-optional">Optional</span>
            </div>
            <p>
              These cookies enable the website to provide enhanced functionality and personalization. They may be 
              set by us or by third-party providers whose services we have added to our pages. If you do not allow 
              these cookies, some or all of these services may not function properly.
            </p>
            <p class="cookie-examples">
              <strong>Examples:</strong> Language preferences, region settings, user interface customization
            </p>
          </div>

          <div class="cookie-type-card">
            <div class="cookie-type-header">
              <h3>Analytics Cookies</h3>
              <span class="cookie-badge cookie-badge-optional">Optional</span>
            </div>
            <p>
              These cookies help us understand how visitors interact with our website by collecting and reporting 
              information anonymously. This helps us improve our website's performance and user experience. The 
              information collected is aggregated and anonymous.
            </p>
            <p class="cookie-examples">
              <strong>Examples:</strong> Page views, time spent on pages, navigation patterns, error tracking
            </p>
          </div>

          <div class="cookie-type-card">
            <div class="cookie-type-header">
              <h3>Marketing Cookies</h3>
              <span class="cookie-badge cookie-badge-optional">Optional</span>
            </div>
            <p>
              These cookies may be set through our site by our advertising partners. They may be used to build a 
              profile of your interests and show you relevant content on other sites. They do not store directly 
              personal information but are based on uniquely identifying your browser and internet device.
            </p>
            <p class="cookie-examples">
              <strong>Examples:</strong> Ad targeting, campaign tracking, conversion measurement
            </p>
          </div>
        </section>

        <section class="cookie-policy-section">
          <h2>Managing Your Cookie Preferences</h2>
          <p>
            You can manage your cookie preferences at any time by clicking the "Cookie Preferences" link in the 
            footer or by accessing the cookie banner that appears when you first visit our website.
          </p>
          <p>
            You can also control cookies through your browser settings. Most browsers allow you to refuse or accept 
            cookies, or to delete existing cookies. However, please note that blocking or deleting cookies may impact 
            your experience on our website.
          </p>
          <div class="cookie-actions">
            <button class="cookie-policy-btn" @click="openCookiePreferences">
              <i class="fas fa-cog"></i> Manage Cookie Preferences
            </button>
          </div>
        </section>

        <section class="cookie-policy-section">
          <h2>Third-Party Cookies</h2>
          <p>
            Some cookies are placed by third-party services that appear on our pages. We do not control the setting 
            of these cookies, so please check the third-party websites for more information about their cookies and 
            how to manage them.
          </p>
        </section>

        <section class="cookie-policy-section">
          <h2>Cookie Retention</h2>
          <p>
            Cookies are stored on your device for different periods depending on their type:
          </p>
          <ul class="cookie-list">
            <li><strong>Session cookies:</strong> These are temporary cookies that are deleted when you close your browser.</li>
            <li><strong>Persistent cookies:</strong> These remain on your device for a set period or until you delete them.</li>
          </ul>
        </section>

        <section class="cookie-policy-section">
          <h2>Your Rights</h2>
          <p>
            Under data protection laws, you have the right to:
          </p>
          <ul class="cookie-list">
            <li>Be informed about the use of cookies</li>
            <li>Give or withdraw consent for non-essential cookies</li>
            <li>Access information about cookies used on our website</li>
            <li>Request deletion of cookie data</li>
          </ul>
        </section>

        <section class="cookie-policy-section">
          <h2>Updates to This Policy</h2>
          <p>
            We may update this Cookie Policy from time to time to reflect changes in our practices or for other 
            operational, legal, or regulatory reasons. We will notify you of any material changes by posting the 
            new Cookie Policy on this page and updating the "Last updated" date.
          </p>
        </section>

        <section class="cookie-policy-section">
          <h2>Contact Us</h2>
          <p>
            If you have any questions about our use of cookies or this Cookie Policy, please contact us through 
            our <router-link to="/help/contact-us">Contact Us</router-link> page.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'CookiePolicy',
  
  setup() {
    const router = useRouter()
    const lastUpdated = ref(new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }))

    const openCookiePreferences = () => {
      // Trigger cookie banner to show customize modal
      // This will be handled by the CookieBanner component
      // For now, we'll just show an alert or trigger a custom event
      window.dispatchEvent(new CustomEvent('openCookiePreferences'))
      
      // If user is on cookie policy page, navigate to home to see banner
      if (router.currentRoute.value.path === '/cookie-policy') {
        router.push('/home')
      }
    }

    onMounted(() => {
      // Scroll to top on mount
      window.scrollTo(0, 0)
    })

    return {
      lastUpdated,
      openCookiePreferences
    }
  }
}
</script>

<style scoped>
.cookie-policy-page {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 40px 20px;
}

.cookie-policy-container {
  max-width: 900px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.cookie-policy-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  text-align: center;
}

.cookie-policy-header h1 {
  margin: 0 0 12px 0;
  font-size: 36px;
  font-weight: 700;
}

.cookie-policy-last-updated {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.cookie-policy-content {
  padding: 40px;
}

.cookie-policy-section {
  margin-bottom: 40px;
}

.cookie-policy-section:last-child {
  margin-bottom: 0;
}

.cookie-policy-section h2 {
  color: #2c3e50;
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

.cookie-policy-section p {
  color: #495057;
  font-size: 16px;
  line-height: 1.8;
  margin: 0 0 16px 0;
}

.cookie-policy-section a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.cookie-policy-section a:hover {
  text-decoration: underline;
}

.cookie-type-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.cookie-type-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.cookie-type-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.cookie-badge {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.cookie-badge-required {
  background: #28a745;
  color: white;
}

.cookie-badge-optional {
  background: #6c757d;
  color: white;
}

.cookie-examples {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #dee2e6;
  font-size: 14px;
  color: #6c757d;
}

.cookie-list {
  margin: 16px 0;
  padding-left: 24px;
  color: #495057;
  line-height: 1.8;
}

.cookie-list li {
  margin-bottom: 8px;
}

.cookie-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.cookie-policy-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cookie-policy-btn:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.cookie-policy-btn i {
  font-size: 18px;
}

/* Responsive */
@media (max-width: 768px) {
  .cookie-policy-page {
    padding: 20px 10px;
  }

  .cookie-policy-header {
    padding: 30px 20px;
  }

  .cookie-policy-header h1 {
    font-size: 28px;
  }

  .cookie-policy-content {
    padding: 30px 20px;
  }

  .cookie-policy-section h2 {
    font-size: 20px;
  }

  .cookie-type-card {
    padding: 20px;
  }
}
</style>

