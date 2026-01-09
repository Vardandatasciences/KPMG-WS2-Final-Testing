import http from '../api/http.js'

// Create API service with methods for different endpoints
const api = {

  // Plans endpoints
  plans: {
    list: (params) => http.get('bcpdrp/plans/', { params }),
    get: (id) => http.get(`bcpdrp/plans/${id}/`),
    create: (data) => http.post('bcpdrp/plans/', data),
    update: (id, data) => http.patch(`bcpdrp/plans/${id}/`, data),
    delete: (id) => http.delete(`bcpdrp/plans/${id}/`),
    getEvaluations: (id) => http.get(`bcpdrp/evaluations/${id}/`),
    approve: (id) => http.post(`bcpdrp/plans/${id}/approve/`),
    reject: (id) => http.post(`bcpdrp/plans/${id}/reject/`),
  },

  // Strategies endpoints
  strategies: {
    list: (params) => http.get('bcpdrp/strategies/', { params }),
  },

  // OCR endpoints
  ocr: {
    plans: (params) => http.get('bcpdrp/ocr/plans/', { params }),
    planDetail: (id) => http.get(`bcpdrp/ocr/plans/${id}/`),
    extract: (id, data) => http.post(`bcpdrp/ocr/plans/${id}/extract/`, data),
    updateStatus: (id, data) => http.patch(`bcpdrp/ocr/plans/${id}/status/`, data),
  },

  // Evaluations endpoints
  evaluations: {
    list: (planId) => http.get(`bcpdrp/evaluations/${planId}/`),
    save: (planId, data) => {
      // Evaluation saves now use background tasks for risk generation, so normal timeout is fine
      return http.post(`bcpdrp/evaluations/${planId}/save/`, data)
    },
  },

  // Risks endpoints
  risks: {
    getPlanRisks: (planId) => http.get(`bcpdrp/plans/${planId}/risks/`),
  },

  // Vendor upload endpoint
  vendorUpload: (data) => http.post('bcpdrp/vendor-upload/', data),

  // Dropdowns endpoint
  dropdowns: (params) => http.get('bcpdrp/dropdowns/', { params }),

  // Plan types endpoints
  planTypes: {
    list: () => http.get('bcpdrp/plan-types/'),
    create: (data) => http.post('bcpdrp/plan-types/create/', data),
    update: (id, data) => http.put(`bcpdrp/plan-types/${id}/update/`, data),
    delete: (id) => http.delete(`bcpdrp/plan-types/${id}/delete/`),
  },
  
  // Questionnaires endpoints
  questionnaires: {
    list: (params) => http.get('bcpdrp/questionnaires/', { params }),
    get: (id) => http.get(`bcpdrp/questionnaires/${id}/`),
    save: (data) => http.post('bcpdrp/questionnaires/save/', data),
    assignments: (params) => http.get('bcpdrp/questionnaires/assignments/', { params }),
    saveAnswers: (assignmentId, data) => http.put(`bcpdrp/questionnaires/assignments/${assignmentId}/save/`, data),
    getDetails: (id) => http.get(`bcpdrp/questionnaires/${id}/`),
    approve: (id) => http.post(`bcpdrp/questionnaires/${id}/approve/`),
    reject: (id) => http.post(`bcpdrp/questionnaires/${id}/reject/`),
  },

  // Questionnaire Workflow endpoints
  questionnaireWorkflow: {
    // Create questionnaire with plan association
    createQuestionnaire: (data) => http.post('bcpdrp/questionnaires/save/', data),
    // Assign questionnaire for testing
    assignQuestionnaire: (data) => http.post('bcpdrp/approvals/assignments/', data),
    // Get workflow status
    getWorkflowStatus: (questionnaireId) => http.get(`bcpdrp/questionnaires/${questionnaireId}/workflow/`),
    // Complete workflow (questionnaire creation + assignment)
    completeWorkflow: (data) => http.post('bcpdrp/questionnaire-workflow/complete/', data),
  },
  // Questionnaire Template endpoints
  questionnaireTemplates: {
    list: (params) => http.get('bcpdrp/questionnaire-templates/', { params }),
    get: (id) => http.get(`bcpdrp/questionnaire-templates/${id}/`),
    save: (data) => http.post('bcpdrp/questionnaire-templates/save/', data),
  },
  // Plan decisions endpoint
  planDecision: (id, data) => http.patch(`bcpdrp/plans/${id}/decision/`, data),

  // Users endpoints
  users: {
    list: (params) => http.get('bcpdrp/users/', { params }),
  },

  // Approvals endpoints
  approvals: {
    list: (params) => http.get('bcpdrp/approvals/', { params }),
    createAssignment: (data) => http.post('bcpdrp/approvals/assignments/', data),
    myApprovals: (params) => http.get('bcpdrp/my-approvals/', { params }),
    updateStatus: (approvalId, data) => http.patch(`bcpdrp/approvals/${approvalId}/status/`, data),
  },

  // Assignment responses endpoints
  assignments: {
    getResponseDetails: (id) => http.get(`bcpdrp/questionnaires/assignments/`, { params: { assignment_response_id: id } }),
    approve: (id) => http.post(`bcpdrp/questionnaires/assignments/${id}/approve/`),
    reject: (id) => http.post(`bcpdrp/questionnaires/assignments/${id}/reject/`),
  },

   // Dashboard endpoints
   dashboard: {
    overview: () => http.get('bcpdrp/dashboard/overview/'),
    kpi: () => http.get('bcpdrp/dashboard/kpi/'),
    plans: () => http.get('bcpdrp/dashboard/plans/'),
    evaluations: () => http.get('bcpdrp/dashboard/evaluations/'),
    evaluationScores: () => http.get('bcpdrp/dashboard/evaluation-scores/'),
    testing: () => http.get('bcpdrp/dashboard/testing/'),
    risks: () => http.get('bcpdrp/dashboard/risks/'),
    temporal: () => http.get('bcpdrp/dashboard/temporal/'),
  },
}

export default api
