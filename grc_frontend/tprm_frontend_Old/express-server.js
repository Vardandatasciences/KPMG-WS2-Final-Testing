// Express.js server configuration for RFP Management System MPA
const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use((req, res, next) => {
  res.setHeader('X-Frame-Options', 'SAMEORIGIN');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  next();
});

// CORS middleware for API routes
app.use('/api', (req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  next();
});

// API proxy to Django backend
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api'
  }
}));

// Static files with caching
app.use(express.static(path.join(__dirname, 'dist'), {
  maxAge: '1y',
  etag: true,
  lastModified: true,
  setHeaders: (res, path) => {
    if (path.match(/\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$/)) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    }
  }
}));

// Route handlers for MPA
app.get('/dashboard', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'dashboard.html'));
});

app.get('/workflow', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'rfp-workflow.html'));
});

app.get('/rfp-dashboard', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'rfp-dashboard.html'));
});

app.get('/vendor-portal/:token', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'vendor-portal.html'));
});

app.get('/approval-management', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'approval-management.html'));
});

app.get('/analytics', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'analytics.html'));
});

app.get('/drafts', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'draft-manager.html'));
});

app.get('/my-approvals', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'my-approvals.html'));
});

app.get('/all-approvals', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'all-approvals.html'));
});

// Root route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// 404 handler
app.use((req, res) => {
  res.status(404).sendFile(path.join(__dirname, 'dist', '404.html'));
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).sendFile(path.join(__dirname, 'dist', '50x.html'));
});

app.listen(PORT, () => {
  console.log(`RFP Management System MPA server running on port ${PORT}`);
  console.log(`Available routes:`);
  console.log(`  - http://localhost:${PORT}/dashboard`);
  console.log(`  - http://localhost:${PORT}/workflow`);
  console.log(`  - http://localhost:${PORT}/rfp-dashboard`);
  console.log(`  - http://localhost:${PORT}/vendor-portal/:token`);
  console.log(`  - http://localhost:${PORT}/approval-management`);
  console.log(`  - http://localhost:${PORT}/analytics`);
  console.log(`  - http://localhost:${PORT}/drafts`);
  console.log(`  - http://localhost:${PORT}/my-approvals`);
  console.log(`  - http://localhost:${PORT}/all-approvals`);
});

