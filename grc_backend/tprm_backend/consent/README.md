# TPRM Consent Management Setup

This module provides consent management functionality for TPRM actions, using separate tables to avoid conflicts with GRC consent system.

## Database Tables

The following tables are created in the TPRM database:

1. **consent_configuration_tprm** - Stores consent configuration for TPRM actions
2. **consent_acceptance_tprm** - Tracks when users accept consent
3. **consent_withdrawal_tprm** - Tracks when users withdraw consent

## Setup Instructions

### Option 1: Using Django Management Command (Recommended)

Run the management command to create tables and insert default configurations:

```bash
cd grc_backend
python manage.py setup_tprm_consent_tables
```

This will:
- Create all three TPRM consent tables
- Insert default consent configurations including "Create SLA"
- Set all configurations to `IsEnabled = 0` (disabled by default)

### Option 2: Using SQL Script

If you prefer to run SQL directly:

1. Connect to your TPRM database
2. Run the SQL script:
   ```bash
   mysql -u your_user -p your_tprm_database < grc_backend/tprm_backend/consent/create_tprm_consent_tables.sql
   ```

Or execute the SQL file contents directly in your database client.

## Default Consent Configurations

The following consent configurations are created by default (all disabled):

- **tprm_create_sla** - Create SLA
- **tprm_update_sla** - Update SLA
- **tprm_delete_sla** - Delete SLA
- **tprm_create_vendor** - Create Vendor
- **tprm_update_vendor** - Update Vendor
- **tprm_create_contract** - Create Contract
- **tprm_update_contract** - Update Contract
- **tprm_create_rfp** - Create RFP
- **tprm_submit_rfp** - Submit RFP
- **tprm_create_risk** - Create Risk Assessment
- **tprm_create_compliance** - Create Compliance Record

## Enabling Consent for SLA Creation

1. Go to **Consent Configuration** page in the admin panel
2. Select **"TPRM Only"** or **"All"** from the consent type dropdown
3. Find **"Create SLA"** in the list
4. Toggle the switch to enable it
5. Optionally edit the consent text
6. Click **"Save All Changes"**

Once enabled, users will see a consent modal when creating an SLA.

## API Endpoints

- `GET /api/tprm/consent/configurations/` - Get all TPRM consent configurations
- `PUT /api/tprm/consent/configurations/<config_id>/` - Update a configuration
- `PUT /api/tprm/consent/configurations/bulk-update/` - Bulk update configurations
- `POST /api/tprm/consent/check-required/` - Check if consent is required
- `POST /api/tprm/consent/accept/` - Record consent acceptance

## Usage in Frontend

```javascript
import { executeWithTPRMConsent, TPRM_CONSENT_ACTIONS } from '@/utils/tprmConsentManager.js';
import TPRMConsentModal from '@/components/Consent/TPRMConsentModal.vue';

// In your component
const consentModalRef = ref(null);

async function showConsentModal(actionType, config) {
  const accepted = await consentModalRef.value.show(actionType, config);
  return accepted;
}

// Wrap your action with consent check
const result = await executeWithTPRMConsent(
  TPRM_CONSENT_ACTIONS.CREATE_SLA,
  async (consentConfig) => {
    // Your action code here
    return await createSLA(slaData);
  },
  showConsentModal
);
```

## Database Connection

The module automatically detects the TPRM database connection:
- First tries to use `connections['tprm']` if available
- Falls back to `connections['default']` if TPRM connection not configured

Make sure your `settings.py` has the TPRM database configured if you want to use a separate database.


