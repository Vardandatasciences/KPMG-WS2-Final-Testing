import { createStore } from 'vuex'
import incidents from './modules/incidents'
import framework from './modules/framework'
import appData   from './modules/appData'

const store = createStore({
  modules: {
    incidents,
    framework,
    appData,
  },
  strict: process.env.NODE_ENV !== 'production'
})

export default store
