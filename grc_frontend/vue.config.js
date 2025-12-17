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
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 30000, // 30 seconds timeout for proxy requests
        proxyTimeout: 30000 // 30 seconds timeout for proxy connection
      }
    },
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false
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
