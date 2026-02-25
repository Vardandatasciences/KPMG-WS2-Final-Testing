# RFI Vendor Invitations & Responses Setup

## Overview

This document describes the RFI vendor invitation and response flow, similar to the RFP flow.

## Database Tables

### rfi_vendor_invitations
Stores invitation records when vendors are selected and URLs are generated.

| Column | Type |
|--------|------|
| invitation_id | bigint PK |
| rfi_id | FK to rfis |
| vendor_id | bigint (nullable) |
| vendor_email | varchar(255) |
| vendor_name | varchar(255) |
| vendor_phone | varchar(50) |
| company_name | varchar(255) |
| invited_date | timestamp |
| invitation_status | enum (CREATED, SENT, ACKNOWLEDGED, SUBMITTED, etc.) |
| unique_token | varchar(255) |
| invitation_url | varchar(500) |
| submission_url | varchar(500) |
| TenantId | int |

### rfi_responses
Stores vendor responses when they submit the RFI form.

| Column | Type |
|--------|------|
| response_id | bigint PK |
| rfi_id | FK to rfis |
| vendor_id | bigint (nullable) |
| invitation_id | bigint (nullable) |
| proposal_data | json |
| submission_status | varchar(20) |
| TenantId | int |
| ... (see models.py for full schema) |

## Running Migrations

```bash
cd grc_backend
python manage.py migrate rfi
```

If the migration fails (e.g., due to existing tables), you may need to:
```bash
python manage.py migrate rfi 0001 --fake   # Fake 0001 if rfis already exists
python manage.py migrate rfi               # Apply 0003
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/tprm/v1/rfi-invitations/generate/ | Generate invitations, store in DB |
| GET | /api/tprm/v1/rfi-invitations/{token}/ | Get RFI details by token (vendor portal) |
| POST | /api/tprm/v1/rfi-invitations/{token}/acknowledge/ | Mark invitation as acknowledged |
| POST | /api/tprm/v1/rfi-responses/ | Submit RFI response from vendor portal |

## Flow

1. **RFI List** → User clicks "Select Vendors" on an RFI
2. **RFI Vendor Selection** → User selects vendors (existing + manual), clicks "Proceed to URL Generation"
3. **RFI URL Generation** → User clicks "Generate URLs" → Backend creates records in `rfi_vendor_invitations`, returns unique URLs
4. **Share URLs** → User copies each URL and shares with vendors
5. **Vendor Portal** → Vendor opens URL (/rfi-vendor-portal/{token}) → Loads RFI by token, fills form, submits
6. **Submission** → Backend stores response in `rfi_responses`, updates invitation status to SUBMITTED
