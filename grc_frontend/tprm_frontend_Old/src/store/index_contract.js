import { createStore } from 'vuex'
import authModule from './modules/auth'

export default createStore({
  modules: {
    auth: authModule
  },
  
  state: {
    loading: false,
    loadingMessage: ''
  },
  
  getters: {
    isLoading: state => state.loading,
    loadingMessage: state => state.loadingMessage
  },
  
  mutations: {
    SET_LOADING(state, { loading, message = '' }) {
      state.loading = loading
      state.loadingMessage = message
    },
    
    CLEAR_AUTH(state) {
      // Global auth clearing for emergency purposes
      localStorage.removeItem('session_token')
    }
  },
  
  actions: {
    setLoading({ commit }, payload) {
      commit('SET_LOADING', payload)
    }
  }
})
