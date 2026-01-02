import http from './http.js'

// Questionnaire API service
export const questionnaireApi = {
  // Get all questionnaires with optional filtering
  async getQuestionnaires(params = {}) {
    const queryParams = new URLSearchParams()
    
    if (params.search) queryParams.append('search', params.search)
    if (params.planType && params.planType !== 'ALL') queryParams.append('plan_type', params.planType)
    if (params.status && params.status !== 'ALL') queryParams.append('status', params.status)
    if (params.owner && params.owner !== 'ALL') queryParams.append('owner', params.owner)
    
    const queryString = queryParams.toString()
    const url = queryString ? `/bcpdrp/questionnaires/?${queryString}` : '/bcpdrp/questionnaires/'
    
    console.log('API Call - URL:', url)
    console.log('API Call - Params:', params)
    
    const response = await http.get(url)
    console.log('API Call - Raw Response:', response)
    
    return response
  },

  // Get detailed questionnaire information
  async getQuestionnaireDetail(questionnaireId) {
    return await http.get(`/bcpdrp/questionnaires/${questionnaireId}/`)
  },


  // Create new questionnaire
  async createQuestionnaire(data) {
    return await http.post('/bcpdrp/questionnaires/', data)
  },

  // Update questionnaire
  async updateQuestionnaire(questionnaireId, data) {
    return await http.patch(`/bcpdrp/questionnaires/${questionnaireId}/`, data)
  },

  // Delete questionnaire
  async deleteQuestionnaire(questionnaireId) {
    return await http.delete(`/bcpdrp/questionnaires/${questionnaireId}/`)
  }
}

export default questionnaireApi
