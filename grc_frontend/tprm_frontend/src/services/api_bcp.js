import http from '../api/http.js'

// Create API service with methods for different endpoints
const api = {

  // Plans endpoints
  plans: {
    list: (params) => http.get('/api/bcpdrp/plans/', { params }),
    get: (id) => http.get(`/api/bcpdrp/plans/${id}/`),
    create: (data) => http.post('/api/bcpdrp/plans/', data),
    update: (id, data) => http.patch(`/api/bcpdrp/plans/${id}/`, data),
    delete: (id) => http.delete(`/api/bcpdrp/plans/${id}/`),
    getEvaluations: (id) => http.get(`/api/bcpdrp/evaluations/${id}/`),
    approve: (id) => http.post(`/api/bcpdrp/plans/${id}/approve/`),
    reject: (id) => http.post(`/api/bcpdrp/plans/${id}/reject/`),
  },

  // Strategies endpoints
  strategies: {
    list: (params) => http.get('/api/bcpdrp/strategies/', { params }),
  },

  // OCR endpoints
  ocr: {
    plans: (params) => http.get('/api/bcpdrp/ocr/plans/', { params }),
    planDetail: (id) => http.get(`/api/bcpdrp/ocr/plans/${id}/`),
    extract: (id, data) => http.post(`/api/bcpdrp/ocr/plans/${id}/extract/`, data),
    updateStatus: (id, data) => http.patch(`/api/bcpdrp/ocr/plans/${id}/status/`, data),
  },

  // Evaluations endpoints
  evaluations: {
    list: (planId) => http.get(`/api/bcpdrp/evaluations/${planId}/`),
    save: (planId, data) => {
      // Evaluation saves now use background tasks for risk generation, so normal timeout is fine
      return http.post(`/api/bcpdrp/evaluations/${planId}/save/`, data)
    },
  },

  // Risks endpoints
  risks: {
    getPlanRisks: (planId) => http.get(`/api/bcpdrp/plans/${planId}/risks/`),
  },

  // Vendor upload endpoint
  vendorUpload: (data) => http.post('/api/bcpdrp/vendor-upload/', data),

  // Dropdowns endpoint
  dropdowns: (params) => http.get('/api/bcpdrp/dropdowns/', { params }),

  // Plan types endpoints
  planTypes: {
    list: () => http.get('/api/bcpdrp/plan-types/'),
    create: (data) => http.post('/api/bcpdrp/plan-types/create/', data),
    update: (id, data) => http.put(`/api/bcpdrp/plan-types/${id}/update/`, data),
    delete: (id) => http.delete(`/api/bcpdrp/plan-types/${id}/delete/`),
  },
  
  // Questionnaires endpoints
  questionnaires: {
    list: (params) => http.get('/api/bcpdrp/questionnaires/', { params }),
    get: (id) => http.get(`/api/bcpdrp/questionnaires/${id}/`),
    save: (data) => http.post('/api/bcpdrp/questionnaires/save/', data),
    assignments: (params) => http.get('/api/bcpdrp/questionnaires/assignments/', { params }),
    saveAnswers: (assignmentId, data) => http.put(`/api/bcpdrp/questionnaires/assignments/${assignmentId}/save/`, data),
    getDetails: (id) => http.get(`/api/bcpdrp/questionnaires/${id}/`),
    approve: (id) => http.post(`/api/bcpdrp/questionnaires/${id}/approve/`),
    reject: (id) => http.post(`/api/bcpdrp/questionnaires/${id}/reject/`),
  },

  // Questionnaire Workflow endpoints
  questionnaireWorkflow: {
    // Create questionnaire with plan association
    createQuestionnaire: (data) => http.post('/api/bcpdrp/questionnaires/save/', data),
    // Assign questionnaire for testing
    assignQuestionnaire: (data) => http.post('/api/bcpdrp/approvals/assignments/', data),
    // Get workflow status
    getWorkflowStatus: (questionnaireId) => http.get(`/api/bcpdrp/questionnaires/${questionnaireId}/workflow/`),
    // Complete workflow (questionnaire creation + assignment)
    completeWorkflow: (data) => http.post('/api/bcpdrp/questionnaire-workflow/complete/', data),
  },
  // Questionnaire Template endpoints
  questionnaireTemplates: {
    list: (params) => http.get('/api/bcpdrp/questionnaire-templates/', { params }),
    get: (id) => http.get(`/api/bcpdrp/questionnaire-templates/${id}/`),
    save: (data) => http.post('/api/bcpdrp/questionnaire-templates/save/', data),
  },
  // Plan decisions endpoint
  planDecision: (id, data) => http.patch(`/api/bcpdrp/plans/${id}/decision/`, data),

  // Users endpoints
  users: {
    list: (params) => http.get('/api/bcpdrp/users/', { params }),
  },

  // Approvals endpoints
  approvals: {
    list: (params) => http.get('/api/bcpdrp/approvals/', { params }),
    createAssignment: (data) => http.post('/api/bcpdrp/approvals/assignments/', data),
    myApprovals: (params) => http.get('/api/bcpdrp/my-approvals/', { params }),
    updateStatus: (approvalId, data) => http.patch(`/api/bcpdrp/approvals/${approvalId}/status/`, data),
  },

  // Assignment responses endpoints
  assignments: {
    getResponseDetails: (id) => http.get(`/api/bcpdrp/questionnaires/assignments/`, { params: { assignment_response_id: id } }),
    approve: (id) => http.post(`/api/bcpdrp/questionnaires/assignments/${id}/approve/`),
    reject: (id) => http.post(`/api/bcpdrp/questionnaires/assignments/${id}/reject/`),
  },

   // Dashboard endpoints
   dashboard: {
    overview: () => http.get('/api/bcpdrp/dashboard/overview/'),
    kpi: () => http.get('/api/bcpdrp/dashboard/kpi/'),
    plans: () => http.get('/api/bcpdrp/dashboard/plans/'),
    evaluations: () => http.get('/api/bcpdrp/dashboard/evaluations/'),
    evaluationScores: () => http.get('/api/bcpdrp/dashboard/evaluation-scores/'),
    testing: () => http.get('/api/bcpdrp/dashboard/testing/'),
    risks: () => http.get('/api/bcpdrp/dashboard/risks/'),
    temporal: () => http.get('/api/bcpdrp/dashboard/temporal/'),
  },
}

export default api
