# Background Processing / Async Architecture Implementation

## Status: IN PROGRESS

This document tracks the implementation of async job processing for risk document uploads.

## Overview

The async architecture decouples Django backend from AI processing, enabling:
- Independent scaling of services
- Prevention of timeout errors
- Better user experience with immediate response
- Foundation for microservice architecture

## Implementation Plan

### Phase 1: Database Model ✅ (Separate file approach)
- [x] Create RiskAssessment model structure
- [ ] Create database migration
- [ ] Add model to models.py properly

### Phase 2: AI Microservice Client ✅
- [x] Create AIMicroserviceClient utility
- [x] Handle service unavailability gracefully
- [x] Support feedback submission

### Phase 3: Backend Endpoints (In Progress)
- [ ] Update upload endpoint for async pattern
- [ ] Create callback endpoint
- [ ] Create status polling endpoint
- [ ] Add S3 upload integration

### Phase 4: Frontend Integration
- [ ] Update frontend to poll for status
- [ ] Add progress indicators
- [ ] Handle async job states

### Phase 5: Local Async Processing (Fallback)
- [ ] Implement local async processing when microservice unavailable
- [ ] Use Django background tasks or threading

## Architecture

```
User Upload → Django → S3 Upload → Create Job → Return job_id (202)
                                    ↓
                            AI Microservice (or Local Async)
                                    ↓
                            Process Document
                                    ↓
                            Callback to Django
                                    ↓
                            Update Job Status
                                    ↓
                            Frontend Polls Status
```

## Files Created/Modified

1. `grc_backend/grc/utils/ai_microservice_client.py` (NEW) ✅
2. `grc_backend/grc/models.py` (MODIFIED - needs proper restoration) ⚠️
3. `grc_backend/grc/routes/Risk/risk_ai_doc.py` (TO MODIFY)
4. `grc_frontend/src/components/Risk/risk_ai.vue` (TO MODIFY)

## Next Steps

1. Restore models.py properly and add RiskAssessment model
2. Create database migration
3. Implement async upload endpoint
4. Implement callback endpoint
5. Implement status endpoint
6. Update frontend

## Note on models.py

The models.py file was accidentally overwritten. It needs to be restored from backup or git history, then the RiskAssessment model should be properly added.

