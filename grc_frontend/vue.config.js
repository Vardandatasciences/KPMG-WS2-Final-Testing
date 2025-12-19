const { defineConfig } = require('@vue/cli-service')
const path = require('path')

module.exports = defineConfig({
  transpileDependencies: [
    // Transpile TPRM frontend dependencies
    /tprm_frontend/,
    'pinia',
    'lucide-vue-next',
    '@tanstack/vue-query',
    '@tiptap',
    'recharts',
    'class-variance-authority',
    'clsx',
    'tailwind-merge',
    'zod'
  ],
  
  // Public path for production builds
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',
  
  // Output directory
  outputDir: 'dist',
  
  // Disable source maps in production for smaller bundle size
  productionSourceMap: false,
  
  devServer: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        timeout: 120000, // 2 minutes timeout for proxy requests (increased for long-running operations)
        proxyTimeout: 120000, // 2 minutes timeout for proxy connection
        onError: (err, req, res) => {
          console.error('Proxy error:', err.message);
        },
        onProxyReq: (proxyReq, req, res) => {
          console.log(`[Proxy] ${req.method} ${req.url} -> ${proxyReq.path}`);
        }
      }
    },
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
        runtimeErrors: (error) => {
          const errorMessage = error.message || '';
          const errorString = error.toString() || '';
          
          // Don't show overlay for timeout errors - they're handled gracefully
          if (errorMessage.includes('Timeout') || errorString.includes('Timeout') || 
              errorMessage.includes('timeout') || errorString.includes('timeout')) {
            console.warn('⚠️ Timeout error suppressed from overlay:', errorMessage);
            return false;
          }
          
          // Don't show overlay for network errors - they're handled gracefully
          if (errorMessage.includes('Network Error') || errorMessage.includes('ERR_NETWORK') ||
              errorString.includes('Network Error') || errorString.includes('ERR_NETWORK')) {
            console.warn('⚠️ Network error suppressed from overlay:', errorMessage);
            return false;
          }
          
          // Don't show overlay for reCAPTCHA errors - they're handled gracefully
          if (errorMessage.includes('recaptcha') || errorString.includes('recaptcha') ||
              errorMessage.includes('grecaptcha') || errorString.includes('grecaptcha') ||
              error.stack?.includes('recaptcha') || error.stack?.includes('recaptcha_en.js')) {
            console.warn('⚠️ reCAPTCHA error suppressed from overlay:', errorMessage);
            return false;
          }
          
          // Don't show overlay for unhandled promise rejections that are timeouts
          if (error.name === 'UnhandledPromiseRejectionWarning' || 
              error.name === 'UnhandledPromiseRejection') {
            if (errorMessage.includes('Timeout') || errorString.includes('Timeout')) {
              console.warn('⚠️ Promise rejection timeout suppressed from overlay:', errorMessage);
              return false;
            }
          }
          
          return true;
        }
      }
    }
  },
  
  // Configure webpack
  configureWebpack: {
    resolve: {
      alias: {
        // Alias for TPRM imports
        '@tprm': path.resolve(__dirname, 'tprm_frontend/src')
      },
      extensions: ['.js', '.jsx', '.vue', '.ts', '.tsx', '.json']
    },
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    }
  },
  
  // Chain webpack for additional configuration
  chainWebpack: config => {
    // Exclude TPRM from ESLint during build (we'll handle it separately)
    config.module
      .rule('eslint')
      .exclude.add(path.resolve(__dirname, 'tprm_frontend'))
      .end()
    
    // Configure vue-loader to handle TypeScript syntax in templates
    config.module
      .rule('vue')
      .test(/\.vue$/)
      .use('vue-loader')
      .tap(options => {
        if (!options) options = {}
        if (!options.compilerOptions) options.compilerOptions = {}
        
        // Make vue-loader more lenient with TypeScript syntax
        options.compilerOptions = {
          ...options.compilerOptions,
          isCustomElement: (tag) => false
        }
        
        // Configure template compiler to handle TypeScript
        options.transpileOptions = {
          transforms: {
            // Disable strict mode for TPRM components
            stripWith: false
          }
        }
        
        return options
      })
    
    // Add rule for TypeScript files from TPRM
    config.module
      .rule('typescript')
      .test(/\.tsx?$/)
      .include.add(path.resolve(__dirname, 'tprm_frontend'))
      .end()
      .use('babel-loader')
      .loader('babel-loader')
      .options({
        presets: [
          ['@babel/preset-env', { targets: 'defaults' }],
          '@babel/preset-typescript'
        ]
      })
  }
})
