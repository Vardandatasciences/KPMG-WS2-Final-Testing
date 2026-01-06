import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  // Only use /tprm/ base path in production builds
  // In development, Vite dev server runs on its own port (3000) without base path
  base: process.env.NODE_ENV === 'production' ? '/tprm/' : '/',
  plugins: [
    vue({
      script: {
        defineModel: true,
        propsDestructure: true
      },
      template: {
        compilerOptions: {
          isCustomElement: (tag) => {
            // Allow Element Plus components and custom vendor components
            return tag.startsWith('el-') || tag.startsWith('vendor_') || tag.includes('-')
          }
        }
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      'vue': 'vue/dist/vue.esm-bundler.js'
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    hmr: {
      overlay: true
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  esbuild: {
    target: 'es2020',
    jsxFactory: 'h',
    jsxFragment: 'Fragment'
  },
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
  },
  build: {
    target: 'es2020',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: 'index.html',
        rfp: 'index-rfp.html',
        vendor: 'index-vendor.html',
        contract: 'index-contract.html'
      },
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['lucide-vue-next'],
          utils: ['axios']
        }
      }
    }
  },
  optimizeDeps: {
    include: [
      'vue', 
      'vue-router', 
      'pinia', 
      'lucide-vue-next', 
      'axios',
      'element-plus',
      '@element-plus/icons-vue',
      'zod'
    ],
    exclude: ['@vite/client', '@vite/env']
  },
  css: {
    preprocessorOptions: {
      css: {
        charset: false
      }
    }
  }
})