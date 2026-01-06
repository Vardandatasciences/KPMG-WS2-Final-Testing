import { createStore } from 'vuex'
import auth from './modules/auth'

export default createStore({
  modules: {
    auth
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
    }
  },
  
  actions: {
    setLoading({ commit }, payload) {
      commit('SET_LOADING', payload)
    }
  }
})
