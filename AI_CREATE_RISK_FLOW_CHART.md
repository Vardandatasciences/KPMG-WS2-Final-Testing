# AI Create Risk Flow Chart

## Complete Flow: Frontend → Backend → AI Service → Response

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND: CreateRisk.vue (grc_frontend/src/components/Risk/CreateRisk.vue)  │
│                                                                             │
│  1. User clicks "AI Suggested" toggle (creationMode = 'ai')                 │
│  2. AI Input Form appears with:                                            │
│     - Title field (or pre-filled from incidentId)                           │
│     - Description field (or pre-filled from incidentId)                     │
│  3. User clicks "Generate Risk Analysis" button                            │
│     → Calls: generateAiSuggestion() function (line 1642)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND: generateAiSuggestion() Function (CreateRisk.vue:1642-1736)      │
│                                                                             │
│  Steps:                                                                     │
│  1. Validate input (title or description required)                          │
│  2. Set isGeneratingAi = true (show loading spinner)                       │
│  3. Prepare analysisData:                                                  │
│     {                                                                       │
│       title: aiInput.title || 'Untitled Incident',                          │
│       description: aiInput.description || aiInput.title                      │
│     }                                                                       │
│  4. Call API: apiService.post(API_ENDPOINTS.ANALYZE_INCIDENT, analysisData)│
│     → Endpoint: /api/analyze-incident/                                      │
│     → Timeout: 80000ms (80 seconds)                                        │
│  5. On success:                                                            │
│     - Call mapAnalysisToForm(response)                                      │
│     - Set aiSuggestionGenerated = true (show form)                          │
│     - Set isGeneratingAi = false                                            │
│  6. On error: Show error popup, offer retry or switch to manual mode        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND: API Configuration (grc_frontend/src/config/api.js:447)           │
│                                                                             │
│  API_ENDPOINTS.ANALYZE_INCIDENT = `${API_BASE_URL}/api/analyze-incident/`   │
│                                                                             │
│  Makes HTTP POST request to backend with:                                   │
│  {                                                                         │
│    title: "...",                                                            │
│    description: "..."                                                       │
│  }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: URL Routing (grc_backend/grc/urls.py:2458)                        │
│                                                                             │
│  path('analyze-incident/', risk_views.analyze_incident, name='analyze-incident')│
│                                                                             │
│  Maps to: grc/routes/Risk/risk_views.py → analyze_incident function        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: View Function (grc_backend/grc/routes/Risk/risk_views.py:1455)    │
│                                                                             │
│  def analyze_incident(request):                                             │
│                                                                             │
│  Steps:                                                                     │
│  1. Extract tenant_id from request (multi-tenancy)                          │
│  2. Log the action (send_log for audit trail)                              │
│  3. Extract incident_description and incident_title from request.data       │
│  4. Validate: at least title or description must be present                 │
│  5. Combine: full_incident = f"Title: {title}\n\nDescription: {desc}"       │
│  6. Call slm_service:                                                      │
│     analysis_result = analyze_security_incident(full_incident)              │
│  7. Validate result is a dict with required fields                         │
│  8. Ensure all required fields present (add empty strings if missing):       │
│     - criticality                                                           │
│     - possibleDamage                                                       │
│     - category                                                             │
│     - riskDescription                                                      │
│     - riskLikelihood                                                       │
│     - riskLikelihoodJustification                                          │
│     - riskImpact                                                           │
│     - riskImpactJustification                                              │
│     - riskExposureRating                                                   │
│     - riskPriority                                                         │
│     - riskMitigation                                                       │
│  9. Synthesize default justifications if AI didn't provide them            │
│  10. Return Response(analysis_result)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: SLM Service (grc_backend/grc/routes/Risk/slm_service.py:141)      │
│                                                                             │
│  def analyze_security_incident(incident_description):                       │
│                                                                             │
│  Steps:                                                                     │
│  1. Get centralized AI service: ai_service = get_ai_service()              │
│  2. Calculate document hash for caching/RAG:                               │
│     document_hash = calculate_document_hash(incident_description)          │
│  3. Optional RAG context retrieval:                                         │
│     - Check if RAG available: is_rag_available()                           │
│     - Retrieve relevant context: retrieve_relevant_context(n_results=3)    │
│     - rag_context_text = json.dumps(rag_context)                           │
│  4. Process with AI:                                                       │
│     response = ai_service.run_task(                                        │
│       task_name="risk.analyze_security_incident",                          │
│       payload={                                                            │
│         "incident_description": incident_description,                      │
│         "rag_context": rag_context_text                                    │
│       },                                                                    │
│       options=AIRequestOptions(                                            │
│         task_name="risk.analyze_security_incident",                        │
│         document_hash=document_hash,                                       │
│         use_cache=True,                                                    │
│         metadata={"rag_chunks_used": len(rag_context)}                     │
│       )                                                                    │
│     )                                                                      │
│  5. Queue for large descriptions (>5000 chars):                            │
│     - Use process_with_queue() for large inputs                           │
│  6. Fallback to generate_fallback_analysis() if AI fails                   │
│  7. Add analysis to RAG knowledge base for future context                  │
│  8. Return analysis dict                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: AI Service (grc_backend/grc/ai/service.py:479)                    │
│                                                                             │
│  def get_ai_service() → AIService():                                        │
│                                                                             │
│  AIService.run_task(task_name, payload, options):                           │
│                                                                             │
│  Steps:                                                                     │
│  1. Get task handler from registry:                                         │
│     - Task name: "risk.analyze_security_incident"                          │
│     - Registry: grc/ai/tasks/__init__.py                                   │
│  2. Apply prompt optimization (few-shot examples, system prompts)          │
│  3. Select AI provider (OpenAI/Ollama) based on config                      │
│  4. Apply caching (if use_cache=True and document_hash provided)            │
│  5. Call task handler function with service, payload, metadata, options     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: AI Task (grc_backend/grc/ai/tasks/risk.py:388)                    │
│                                                                             │
│  def analyze_security_incident_task(service, payload, metadata, options):    │
│                                                                             │
│  Steps:                                                                     │
│  1. Extract incident_description and rag_context from payload              │
│  2. Build comprehensive prompt with:                                        │
│     - System instructions (GRC expert persona)                              │
│     - Incident description                                                  │
│     - RAG context (if available)                                            │
│     - AI reasoning instructions                                            │
│     - Risk title instructions                                              │
│     - Velocity instructions                                                │
│     - Required JSON structure (24 fields):                                 │
│       * criticality, criticalityJustification                              │
│       * possibleDamage, possibleDamageJustification                        │
│       * category, categoryJustification                                    │
│       * riskDescription, riskDescriptionJustification                      │
│       * riskLikelihood, riskLikelihoodJustification                        │
│       * riskImpact, riskImpactJustification                                │
│       * velocityScore, velocityJustification                               │
│       * riskExposureRating, riskPriority, riskPriorityJustification         │
│       * riskAppetite                                                       │
│       * riskMitigation (array), riskMitigationJustification                 │
│       * functionalArea, functionalAreaJustification                        │
│       * confidenceScore, confidenceJustification                           │
│       * frameworkReference                                                 │
│       * aiReasoning (cross-referencing format)                             │
│       * perFieldRationale (dict with field-specific rationale)              │
│  3. Call _generate_json(service, task_name, prompt, options)               │
│     - This calls the AI model (OpenAI or Ollama)                           │
│     - Returns JSON response                                                │
│  4. Normalize response: _normalize_risk_analysis_response(result)           │
│  5. Validate all required fields present                                   │
│  6. Return normalized dict                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI MODEL (OpenAI GPT-4o-mini or Ollama)                                    │
│                                                                             │
│  Processes the prompt and returns JSON with risk analysis fields            │
│                                                                             │
│  Response includes:                                                         │
│  - Risk field values (criticality, likelihood, impact, etc.)                │
│  - Justifications for each field                                           │
│  - AI reasoning with cross-references                                       │
│  - Per-field rationale                                                     │
│  - Confidence scores                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RESPONSE FLOW (Back to Frontend)                                           │
│                                                                             │
│  1. AI Task returns normalized dict to AI Service                           │
│  2. AI Service returns to slm_service.analyze_security_incident()          │
│  3. slm_service returns to risk_views.analyze_incident()                   │
│  4. risk_views returns Response(analysis_result) to frontend                │
│  5. Frontend receives response in generateAiSuggestion()                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND: mapAnalysisToForm() (CreateRisk.vue:1738)                        │
│                                                                             │
│  Maps AI response to form fields:                                           │
│  - newRisk.Criticality = response.criticality                                │
│  - newRisk.Category = response.category                                      │
│  - newRisk.RiskDescription = response.riskDescription                       │
│  - newRisk.RiskLikelihood = response.riskLikelihood                         │
│  - newRisk.RiskImpact = response.riskImpact                                 │
│  - newRisk.RiskExposureRating = response.riskExposureRating                 │
│  - newRisk.RiskPriority = response.riskPriority                             │
│  - newRisk.RiskMitigation = response.riskMitigation                         │
│  - newRisk.BusinessImpact = response.businessImpact                         │
│  - newRisk.functionalArea = response.functionalArea                         │
│                                                                             │
│  Store justifications for AI badges:                                        │
│  - riskJustifications.criticality = response.criticalityJustification      │
│  - riskJustifications.likelihood = response.riskLikelihoodJustification    │
│  - riskJustifications.impact = response.riskImpactJustification            │
│  - etc.                                                                    │
│                                                                             │
│  Show form with AI-generated values and AI justification badges             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER REVIEW & SUBMIT                                                        │
│                                                                             │
│  1. User reviews AI-generated values in the form                            │
│  2. User can hover over AI badges to see justifications                     │
│  3. User can edit any field before submitting                               │
│  4. User clicks "Create Risk" button                                        │
│  5. Form submits to backend risk creation endpoint                          │
│  6. Risk is saved to database                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Files Involved

### Frontend Files
1. **grc_frontend/src/components/Risk/CreateRisk.vue**
   - Lines 68-116: AI Input Form
   - Lines 1642-1736: generateAiSuggestion() function
   - Lines 1738+: mapAnalysisToForm() function

2. **grc_frontend/src/config/api.js**
   - Line 447: ANALYZE_INCIDENT endpoint definition

### Backend Files
1. **grc_backend/grc/urls.py**
   - Line 2458: URL mapping for analyze-incident

2. **grc_backend/grc/routes/Risk/risk_views.py**
   - Lines 1455-1557: analyze_incident() view function

3. **grc_backend/grc/routes/Risk/slm_service.py**
   - Lines 141-236: analyze_security_incident() service function
   - Lines 239-303: analyze_risk_comprehensive() function

4. **grc_backend/grc/ai/service.py**
   - Line 479: get_ai_service() function
   - AIService class: run_task() method

5. **grc_backend/grc/ai/tasks/risk.py**
   - Lines 388-487: analyze_security_incident_task() AI task
   - Lines 488+: _normalize_risk_analysis_response() function

6. **grc_backend/grc/ai/tasks/__init__.py**
   - Task registry mapping task names to handler functions

## AI Prompt Template

The AI task uses a comprehensive prompt that includes:
- System persona: Senior GRC and Enterprise Risk Management expert
- Incident description
- RAG context from previous analyses
- AI reasoning instructions
- Risk title instructions
- Velocity instructions
- Required JSON structure with 24 fields
- Validation checklist

## Data Flow Summary

**Request Flow:**
```
User Input → CreateRisk.vue → generateAiSuggestion() 
→ API POST /api/analyze-incident/ 
→ risk_views.analyze_incident() 
→ slm_service.analyze_security_incident() 
→ AI Service.run_task() 
→ AI Task: analyze_security_incident_task() 
→ AI Model (OpenAI/Ollama)
```

**Response Flow:**
```
AI Model Response → AI Task normalization 
→ AI Service → slm_service 
→ risk_views → HTTP Response 
→ Frontend mapAnalysisToForm() 
→ Form populated with AI values
```

## Features

- **Multi-tenancy**: Tenant ID extracted and validated at each layer
- **Caching**: Document hash-based caching to avoid re-processing same input
- **RAG**: Retrieval Augmented Generation for context from previous analyses
- **Fallback**: Comprehensive fallback analysis if AI fails
- **Justifications**: AI provides rationale for each field value
- **Queue Processing**: Large descriptions (>5000 chars) processed via queue
- **Error Handling**: Robust error handling with user-friendly messages
- **Audit Logging**: All actions logged for compliance
