require("dotenv").config();
const express = require('express');
const multer = require('multer');
const fs = require("fs");
const S3 = require("aws-sdk/clients/s3");
const CloudWatchLogs = require("aws-sdk/clients/cloudwatchlogs");
const bodyParser = require('body-parser');
const cors = require('cors');
const htmlPdf = require('html-pdf-node');

// Configure AWS S3
const bucketName = process.env.AWS_BUCKET_NAME;           // vardaanwebsites (legacy)
const grcBucketName = process.env.GRC_BUCKET_NAME;        // grc-prod-uploads (new)
const region = process.env.AWS_REGION;

if (!bucketName || !grcBucketName || !region) {
  console.error('❌ Missing required env vars: AWS_BUCKET_NAME, GRC_BUCKET_NAME, AWS_REGION');
  process.exit(1);
}

const isProduction = (process.env.NODE_ENV || 'development') === 'production';
const s3 = new S3({ region }); // Uses IAM role automatically


// Configure AWS CloudWatch Logs
const cloudWatchLogsEnabled = process.env.CLOUDWATCH_LOGS_ENABLED === 'true';
const logGroupName = process.env.CLOUDWATCH_LOG_GROUP_NAME || 's3-microservice';
const logStreamName = process.env.CLOUDWATCH_LOG_STREAM_NAME || `s3-microservice-${Date.now()}`;

let cloudWatchLogs = null;
let logSequenceToken = null;
let logBuffer = [];
const LOG_BUFFER_SIZE = 10; // Send logs in batches
const LOG_BUFFER_TIMEOUT = 5000; // 5 seconds

if (cloudWatchLogsEnabled) {
  cloudWatchLogs = new CloudWatchLogs({ region });

  // Create log group if it doesn't exist
  cloudWatchLogs.createLogGroup({ logGroupName }, (err) => {
    if (err && err.code !== 'ResourceAlreadyExistsException') {
      log.error('Failed to create CloudWatch log group', { error: err.message, code: err.code });
    } else {
      log.info('CloudWatch log group ready', { logGroupName });
    }
  });

  // Create log stream
  cloudWatchLogs.createLogStream({ logGroupName, logStreamName }, (err) => {
    if (err && err.code !== 'ResourceAlreadyExistsException') {
      log.error('Failed to create CloudWatch log stream', { error: err.message, code: err.code });
    } else {
      log.info('CloudWatch log stream ready', { logStreamName });
    }
  });
}

// CloudWatch Logger
class CloudWatchLogger {
  constructor() {
    this.buffer = [];
    this.flushTimer = null;
  }

  async sendLogs() {
    if (!cloudWatchLogs || this.buffer.length === 0) return;

    const logEvents = this.buffer.map(log => ({
      message: log.message,
      timestamp: log.timestamp,
    }));

    const params = {
      logGroupName,
      logStreamName,
      logEvents,
    };

    if (logSequenceToken) {
      params.sequenceToken = logSequenceToken;
    }

    try {
      const result = await cloudWatchLogs.putLogEvents(params).promise();
      logSequenceToken = result.nextSequenceToken;
      this.buffer = [];
    } catch (error) {
      if (error.code === 'InvalidSequenceTokenException') {
        // Retry with the correct sequence token
        const match = error.message.match(/The next expected sequenceToken is: (\w+)/);
        if (match) {
          logSequenceToken = match[1];
          return this.sendLogs(); // Retry
        }
      }
      // Use console.error to avoid recursion
      console.error('Failed to send logs to CloudWatch:', error);
    }
  }

  addLog(level, message, metadata = {}) {
    const timestamp = Date.now();
    const logMessage = JSON.stringify({
      level,
      message,
      timestamp: new Date(timestamp).toISOString(),
      service: 's3-microservice',
      ...metadata,
    });

    // Always log to console
    const consoleMessage = `[${level.toUpperCase()}] ${message}${Object.keys(metadata).length > 0 ? ' ' + JSON.stringify(metadata) : ''}`;

    if (level === 'error') {
      console.error(consoleMessage);
    } else if (level === 'warn') {
      console.warn(consoleMessage);
    } else {
      console.log(consoleMessage);
    }

    // Add to CloudWatch buffer if enabled
    if (cloudWatchLogs) {
      this.buffer.push({
        message: logMessage,
        timestamp,
      });

      // Flush if buffer is full
      if (this.buffer.length >= LOG_BUFFER_SIZE) {
        this.sendLogs();
      } else {
        // Set timer to flush after timeout
        if (this.flushTimer) {
          clearTimeout(this.flushTimer);
        }
        this.flushTimer = setTimeout(() => this.sendLogs(), LOG_BUFFER_TIMEOUT);
      }
    }
  }

  async flush() {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
    await this.sendLogs();
  }
}

const logger = new CloudWatchLogger();

// Helper functions for logging
const log = {
  info: (message, metadata) => logger.addLog('info', message, metadata),
  error: (message, metadata) => logger.addLog('error', message, metadata),
  warn: (message, metadata) => logger.addLog('warn', message, metadata),
  debug: (message, metadata) => {
    if (!isProduction) {
      logger.addLog('debug', message, metadata);
    }
  },
};

// ============================================================================
// CRASH PREVENTION: Unhandled Error & Rejection Handlers
// ============================================================================

// Handle unhandled promise rejections (prevents crashes)
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ UNHANDLED REJECTION - Preventing crash:', reason);
  console.error('Promise:', promise);
  // Log but don't crash - let the application continue
  logger.addLog('error', 'Unhandled Promise Rejection', {
    reason: reason?.toString(),
    stack: reason?.stack
  });
});

// Handle uncaught exceptions (last resort - log and exit gracefully)
process.on('uncaughtException', (error) => {
  console.error('❌ UNCAUGHT EXCEPTION - Critical error:', error);
  logger.addLog('error', 'Uncaught Exception', {
    error: error.message,
    stack: error.stack
  });
  // Give time for logs to flush, then exit
  setTimeout(() => {
    process.exit(1);
  }, 1000);
});

// Note: SIGTERM and SIGINT handlers are set up later in the file

// Express app setup
const app = express();
const PORT = process.env.PORT || 3000;

// ============================================================================
// API KEY AUTH FOR ALL ROUTES (protects S3 microservice)
// ============================================================================

const API_KEY = process.env.S3_MICRO_API_KEY;

app.use((req, res, next) => {
  // If no key configured, don't block (useful in local/dev). In prod, set S3_MICRO_API_KEY.
  if (!API_KEY) {
    return next();
  }

  const key = req.headers['x-api-key'];

  if (!key || key !== API_KEY) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
    });
  }

  next();
});

// Production-ready middleware for health checks
app.get('/', (req, res) => {
    res.json({
      status: 'healthy',
      service: 'S3 Microservice',
      version: '1.0.1',
      environment: process.env.NODE_ENV || 'development',
      timestamp: new Date().toISOString(),
      pdfSupport: 'UPDATED - html-pdf-node integration complete',
      endpoints: [
        'GET /health',
        'POST /api/upload/:userId/:fileName',
        'GET /api/download?s3Key=...&fileName=...',
        'POST /api/export/:type/:userId/:fileName (types: json, csv, xml, txt, pdf)'
      ]
    });
  });

// Configure multer for file uploads
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 100 * 1024 * 1024, // 100MB limit
  }
});

// Middleware
app.use(cors({
  origin: isProduction ? process.env.ALLOWED_ORIGINS?.split(',') : '*',
  credentials: true
}));

// Body parser with limits to prevent memory issues
const MAX_REQUEST_SIZE = process.env.MAX_REQUEST_SIZE || '50mb';
app.use(bodyParser.json({
  limit: MAX_REQUEST_SIZE,
  verify: (req, res, buf) => {
    // Check request size before parsing
    if (buf.length > 50 * 1024 * 1024) { // 50MB
      throw new Error('Request payload too large');
    }
  }
}));
app.use(bodyParser.urlencoded({
  extended: true,
  limit: MAX_REQUEST_SIZE
}));

// Add request logging (always enabled for debugging)
app.use((req, res, next) => {
  log.info('Incoming request', {
    method: req.method,
    path: req.path,
    ip: req.ip,
    userAgent: req.get('user-agent') || 'unknown'
  });
  next();
});

// Content type mapping
const CONTENT_TYPES = {
  'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'pdf': 'application/pdf',
  'csv': 'text/csv',
  'json': 'application/json',
  'xml': 'application/xml',
  'txt': 'text/plain',
  'doc': 'application/msword',
  'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'jpg': 'image/jpeg',
  'jpeg': 'image/jpeg',
  'png': 'image/png'
};

// Helper function to generate unique file name
function generateFileName(originalName, userId) {
  const timestamp = Date.now();
  const randomString = Math.random().toString(36).substring(2, 8);
  const extension = originalName.split('.').pop();
  const nameWithoutExt = originalName.replace(/\.[^/.]+$/, "");

  return `${userId}_${timestamp}_${randomString}_${nameWithoutExt}.${extension}`;
}

// Upload file to S3
async function generateDownloadUrl({ bucket, key, fileName, expiresIn = 900, disposition = 'attachment' }) {
    try {
      const safeDisposition = (disposition || 'attachment').toLowerCase(); // attachment | inline

      const params = {
        Bucket: bucket,
        Key: key,
        Expires: Number(expiresIn),
        ResponseContentDisposition: `${safeDisposition}; filename="${fileName}"`
      };

      const downloadUrl = s3.getSignedUrl('getObject', params);

      return {
        success: true,
        downloadUrl,
        fileName,
        expiresIn: Number(expiresIn)
      };
    } catch (error) {
      log.error('Download URL Generation Error', { error: error.message, code: error.code, key, bucket });
      throw new Error(`Failed to generate download URL: ${error.message}`);
    }
  }

// Generate download URL
async function generateDownloadUrlLegacy(s3Key, fileName, expiresIn = 3600) {
  try {
    const params = {
      Bucket: bucketName,
      Key: s3Key,
      Expires: expiresIn,
      ResponseContentDisposition: `attachment; filename="${fileName}"`
    };

    const downloadUrl = s3.getSignedUrl('getObject', params);

    return {
      success: true,
      downloadUrl: downloadUrl,
      fileName: fileName,
      expiresIn: expiresIn
    };
  } catch (error) {
    log.error('Download URL Generation Error', {
      error: error.message,
      code: error.code,
      s3Key,
      fileName
    });
    throw new Error(`Failed to generate download URL: ${error.message}`);
  }
}

// Generate PDF from data
async function generatePDF(data) {
  try {
    // Create HTML content for the PDF
    const htmlContent = createPDFHTML(data);

    // Configure PDF options
    const options = {
      format: 'A4',
      margin: {
        top: '20mm',
        right: '20mm',
        bottom: '20mm',
        left: '20mm'
      },
      printBackground: true
    };

    // Generate PDF
    const pdfBuffer = await htmlPdf.generatePdf({ content: htmlContent }, options);

    return pdfBuffer;
  } catch (error) {
    log.error('PDF Generation Error', {
      error: error.message,
      stack: error.stack
    });
    throw new Error(`Failed to generate PDF: ${error.message}`);
  }
}

// Create HTML content for PDF
function createPDFHTML(data) {
  const isArray = Array.isArray(data);
  const items = isArray ? data : [data];

  const tableRows = items.map((item, index) => {
    const cells = Object.entries(item).map(([key, value]) =>
      `<td style="border: 1px solid #ddd; padding: 8px; text-align: left;">${value}</td>`
    ).join('');

    return `
      <tr>
        <td style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold;">${index + 1}</td>
        ${cells}
      </tr>
    `;
  }).join('');

  const headers = items.length > 0 ? Object.keys(items[0]) : [];
  const headerCells = headers.map(header =>
    `<th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #f2f2f2; font-weight: bold;">${header}</th>`
  ).join('');

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Data Export</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 20px;
          color: #333;
        }
        .header {
          text-align: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #007bff;
          padding-bottom: 10px;
        }
        .header h1 {
          color: #007bff;
          margin: 0;
          font-size: 24px;
        }
        .header p {
          margin: 5px 0 0 0;
          color: #666;
          font-size: 14px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }
        th, td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #f2f2f2;
          font-weight: bold;
        }
        .footer {
          margin-top: 30px;
          text-align: center;
          font-size: 12px;
          color: #666;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>Data Export Report</h1>
        <p>Generated on ${new Date().toLocaleString()}</p>
        <p>Total Records: ${items.length}</p>
      </div>

      <table>
        <thead>
          <tr>
            <th style="border: 1px solid #ddd; padding: 12px; text-align: center; background-color: #f2f2f2; font-weight: bold;">#</th>
            ${headerCells}
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>

      <div class="footer">
        <p>This document was automatically generated by the S3 Microservice</p>
      </div>
    </body>
    </html>
  `;
}

// Export data to different formats
async function exportData(data, format) {
  try {
    switch (format.toLowerCase()) {
      case 'json':
        return {
          buffer: Buffer.from(JSON.stringify(data, null, 2)),
          contentType: CONTENT_TYPES.json,
          extension: 'json'
        };

      case 'csv':
        if (!Array.isArray(data) || data.length === 0) {
          throw new Error('CSV export requires array data');
        }

        const headers = Object.keys(data[0]);
        const csvContent = [
          headers.join(','),
          ...data.map(row =>
            headers.map(header =>
              JSON.stringify(row[header] || '')
            ).join(',')
          )
        ].join('\n');

        return {
          buffer: Buffer.from(csvContent),
          contentType: CONTENT_TYPES.csv,
          extension: 'csv'
        };

      case 'xml':
        const xmlData = Array.isArray(data)
          ? `<?xml version="1.0" encoding="UTF-8"?>\n<root>\n${data.map((item, index) =>
              `  <item_${index}>\n${Object.entries(item).map(([key, value]) =>
                `    <${key}>${value}</${key}>`
              ).join('\n')}\n  </item_${index}>`
            ).join('\n')}\n</root>`
          : `<?xml version="1.0" encoding="UTF-8"?>\n<root>\n${Object.entries(data).map(([key, value]) =>
              `  <${key}>${value}</${key}>`
            ).join('\n')}\n</root>`;

        return {
          buffer: Buffer.from(xmlData),
          contentType: CONTENT_TYPES.xml,
          extension: 'xml'
        };

      case 'txt':
        const txtContent = Array.isArray(data)
          ? data.map((item, index) =>
              `Item ${index + 1}:\n${Object.entries(item).map(([key, value]) =>
                `  ${key}: ${value}`
              ).join('\n')}`
            ).join('\n\n')
          : Object.entries(data).map(([key, value]) => `${key}: ${value}`).join('\n');

        return {
          buffer: Buffer.from(txtContent),
          contentType: CONTENT_TYPES.txt,
          extension: 'txt'
        };

      case 'pdf':
        const pdfBuffer = await generatePDF(data);
        return {
          buffer: pdfBuffer,
          contentType: CONTENT_TYPES.pdf,
          extension: 'pdf'
        };

      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  } catch (error) {
    log.error('Export Error', {
      error: error.message,
      format,
      stack: error.stack
    });
    throw new Error(`Failed to export data: ${error.message}`);
  }
}

// API Routes

// Enhanced health check with memory info
app.get('/health', (req, res) => {
  const memUsage = process.memoryUsage();
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: {
      used: Math.round(memUsage.heapUsed / 1024 / 1024) + 'MB',
      total: Math.round(memUsage.heapTotal / 1024 / 1024) + 'MB',
      rss: Math.round(memUsage.rss / 1024 / 1024) + 'MB'
    },
    nodeVersion: process.version,
    environment: process.env.NODE_ENV || 'development'
  };

  // Check if memory usage is too high (warn if > 80% of heap)
  const heapUsedPercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
  if (heapUsedPercent > 80) {
    health.status = 'degraded';
    health.warning = 'High memory usage detected';
  }

  res.json(health);
});

app.post('/presign-get', async (req, res) => {
    try {
      const { bucket, key, fileName, expiresIn = 900, disposition = 'attachment' } = req.body;

      if (!bucket || !key || !fileName) {
        return res.status(400).json({ success: false, error: 'bucket, key, fileName are required' });
      }

      const result = await generateDownloadUrl({ bucket, key, fileName, expiresIn, disposition });
      return res.json({ success: true, url: result.downloadUrl, expiresIn: result.expiresIn });
    } catch (e) {
      return res.status(500).json({ success: false, error: e.message });
    }
  });

async function uploadToS3({ bucket, key, fileBuffer, contentType }) {
  try {
    const uploadParams = {
      Bucket: bucket,
      Key: key,
      Body: fileBuffer,
      ContentType: contentType,
      ACL: 'private'
    };

    const uploadResult = await s3.upload(uploadParams).promise();

    return {
      success: true,
      key: uploadResult.Key,
      bucket: uploadResult.Bucket,
      url: uploadResult.Location // keep for legacy responses if needed
    };
  } catch (error) {
    log.error('S3 Upload Error', {
      error: error.message,
      code: error.code,
      key,
      bucket
    });
    throw new Error(`Failed to upload to S3: ${error.message}`);
  }
}

// Upload endpoint

app.post('/api/upload/:userId/:fileName', upload.single('file'), async (req, res) => {
  const startTime = Date.now();
  try {
    const { userId, fileName } = req.params;

    // NEW inputs
    const mode = (req.query.mode || 'legacy').toLowerCase(); // legacy | secure
    const product = (req.body.product || 'legacy').toLowerCase(); // riskavaire etc
    const tenantId = req.body.tenant_id || userId;
    const module = (req.body.module || 'uploads').toLowerCase();

    if (!req.file) {
      return res.status(400).json({ success: false, error: 'No file uploaded' });
    }

    const extension = fileName.split('.').pop().toLowerCase();
    const contentType = CONTENT_TYPES[extension] || req.file.mimetype || 'application/octet-stream';

    // Decide bucket
    const targetBucket = (mode === 'secure' && product === 'riskavaire')
      ? grcBucketName
      : bucketName;

    // Decide key
    const safeName = fileName.replace(/[^a-zA-Z0-9._-]/g, "_");
    const key = (mode === 'secure' && product === 'riskavaire')
      ? `${product}/tenant-${tenantId}/${module}/${Date.now()}_${safeName}`
      : generateFileName(fileName, userId); // keep legacy behavior

    const uploadResult = await uploadToS3({
      bucket: targetBucket,
      key,
      fileBuffer: req.file.buffer,
      contentType
    });

    const operation_id = `${Date.now()}_${Math.random().toString(16).slice(2)}`;

    // ✅ SECURE RESPONSE (new flow)
    if (mode === 'secure') {
      return res.json({
        success: true,
        bucket: uploadResult.bucket,
        key: uploadResult.key,
        operation_id
      });
    }

    // ✅ LEGACY RESPONSE (old flow)
    // Keep compatibility for other products expecting url etc.
    return res.json({
      success: true,
      file: {
        originalName: fileName,
        storedName: key,
        url: `s3://${uploadResult.bucket}/${uploadResult.key}`, // or keep uploadResult.Location if you want
        s3Key: uploadResult.key,
        bucket: uploadResult.bucket,
        size: req.file.size,
        contentType,
        userId,
        uploadedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});




// Download endpoint (updated to use query parameters for s3Key and fileName)

app.get('/api/download', async (req, res) => {
  try {
    const key = req.query.s3Key;
    const fileName = req.query.fileName;
    const bucket = req.query.bucket || bucketName;
    const expiresIn = req.query.expires ? parseInt(req.query.expires) : 900;

    if (!key || !fileName) {
      return res.status(400).json({ success: false, error: 'Missing s3Key or fileName' });
    }

    const downloadResult = await generateDownloadUrl({ bucket, key, fileName, expiresIn });

    res.json({ success: true, downloadUrl: downloadResult.downloadUrl, fileName, expiresIn });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});


app.post('/presign-get', async (req, res) => {
  try {
    const { bucket, key, fileName, expiresIn = 900, disposition = 'attachment' } = req.body;
    if (!bucket || !key || !fileName) {
      return res.status(400).json({ success: false, error: 'bucket, key, fileName are required' });
    }

    // ✅ validate existence
    try {
      await s3.headObject({ Bucket: bucket, Key: key }).promise();
    } catch (e) {
      if (e.code === 'NotFound' || e.statusCode === 404) {
        return res.status(404).json({ success: false, error: 'Object not found', bucket, key });
      }
      throw e;
    }

    const result = await generateDownloadUrl({ bucket, key, fileName, expiresIn, disposition });
    return res.json({ success: true, url: result.downloadUrl, expiresIn: result.expiresIn });
  } catch (e) {
    return res.status(500).json({ success: false, error: e.message });
  }
});












// Export endpoint with enhanced error handling
app.post('/api/export/:type/:userId/:fileName', async (req, res) => {
  const startTime = Date.now();
  let exportResult = null;

  try {
    const { type, userId, fileName } = req.params;
    const { data } = req.body;

    // Validate input
    if (!data) {
      log.warn('Export request with no data', { type, userId, fileName });
      return res.status(400).json({
        success: false,
        error: 'No data provided for export'
      });
    }

    // Validate format
    const supportedFormats = ['json', 'csv', 'xml', 'txt', 'pdf'];
    if (!supportedFormats.includes(type.toLowerCase())) {
      log.warn('Unsupported export format', { type, userId, fileName });
      return res.status(400).json({
        success: false,
        error: `Unsupported format: ${type}. Supported formats: ${supportedFormats.join(', ')}`
      });
    }

    // Validate data size (prevent memory issues)
    const dataSize = JSON.stringify(data).length;
    const MAX_DATA_SIZE = 10 * 1024 * 1024; // 10MB
    if (dataSize > MAX_DATA_SIZE) {
      log.warn('Export data too large', { type, userId, fileName, dataSize });
      return res.status(400).json({
        success: false,
        error: `Data size (${Math.round(dataSize / 1024)}KB) exceeds maximum allowed size (${MAX_DATA_SIZE / 1024 / 1024}MB)`
      });
    }

    log.info('Export request received', { type, userId, fileName, dataSize });

    // Export data to specified format with timeout
    const exportPromise = exportData(data, type);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Export operation timed out')), 300000) // 5 min timeout
    );

    exportResult = await Promise.race([exportPromise, timeoutPromise]);

    // Generate file name with proper extension
    const nameWithoutExt = fileName.replace(/\.[^/.]+$/, "");
    const exportFileName = `${nameWithoutExt}.${exportResult.extension}`;
    const uniqueFileName = generateFileName(exportFileName, userId);

    log.info('Export data processed, uploading to S3', {
      type,
      fileName: uniqueFileName,
      size: exportResult.buffer.length
    });

    // Upload exported file to S3 with timeout

    const uploadPromise = uploadToS3({
  bucket: bucketName,              // exports should stay in legacy bucket unless you want otherwise
  key: uniqueFileName,
  fileBuffer: exportResult.buffer,
  contentType: exportResult.contentType
});


    const uploadTimeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('S3 upload timed out')), 120000) // 2 min timeout
    );

    const uploadResult = await Promise.race([uploadPromise, uploadTimeoutPromise]);

    // Generate download URL for exported file

    const downloadResult = await generateDownloadUrlLegacy(uploadResult.key, uniqueFileName, 3600);
    const duration = Date.now() - startTime;
    log.info('Export completed successfully', {
      type,
      userId,
      fileName: uniqueFileName,
      duration: `${duration}ms`,
      size: exportResult.buffer.length
    });

    res.json({
      success: true,
      export: {
        format: type,
        originalName: exportFileName,
        storedName: uniqueFileName,
        url: uploadResult.url,
        s3Key: uploadResult.key,
        bucket: uploadResult.bucket,
        size: exportResult.buffer.length,
        contentType: exportResult.contentType,
        userId: userId,
        recordCount: Array.isArray(data) ? data.length : 1,
        exportedAt: new Date().toISOString(),
        downloadUrl: downloadResult.downloadUrl
      }
    });
  } catch (error) {
    const duration = Date.now() - startTime;
    const errorMessage = error.message || 'Unknown error';

    log.error('Export endpoint error', {
      error: errorMessage,
      type: req.params?.type,
      userId: req.params?.userId,
      fileName: req.params?.fileName,
      duration: `${duration}ms`,
      stack: error.stack
    });

    // Clean up if export result was created but upload failed
    if (exportResult && exportResult.buffer) {
      exportResult.buffer = null; // Help GC
    }

    // Return appropriate status code
    const statusCode = errorMessage.includes('timeout') ? 504 :
                      errorMessage.includes('size') ? 400 : 500;

    res.status(statusCode).json({
      success: false,
      error: isProduction ? 'Export operation failed. Please try again.' : errorMessage
    });
  }
});

// Enhanced error handler (prevents crashes)
app.use((err, req, res, next) => {
  // Don't log stack traces in production for security
  const errorDetails = isProduction ? {
    error: err.message,
    path: req.path,
    method: req.method
  } : {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    ip: req.ip
  };

  log.error('Global error handler', errorDetails);

  // Handle specific error types
  let statusCode = 500;
  let errorMessage = 'Internal Server Error';

  if (err.message && err.message.includes('payload too large')) {
    statusCode = 413;
    errorMessage = 'Request payload too large';
  } else if (err.message && err.message.includes('timeout')) {
    statusCode = 504;
    errorMessage = 'Request timeout';
  } else if (!isProduction) {
    errorMessage = err.message;
  }

  // Ensure response hasn't been sent
  if (!res.headersSent) {
    res.status(statusCode).json({
      success: false,
      error: errorMessage,
      ...(isProduction ? {} : { details: err.message })
    });
  }
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    availableEndpoints: [
      'GET /health',
      'POST /api/upload/:userId/:fileName',
      'GET /api/download?s3Key=...&fileName=...',
      'POST /api/export/:type/:userId/:fileName (types: json, csv, xml, txt, pdf)'
    ]
  });
});

// Explicitly bind to 0.0.0.0 to accept connections from all interfaces (required for AWS)
const server = app.listen(PORT, '0.0.0.0', () => {
  log.info('S3 Microservice started successfully', {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    cloudWatchEnabled: cloudWatchLogsEnabled,
    logGroupName: cloudWatchLogsEnabled ? logGroupName : null,
    logStreamName: cloudWatchLogsEnabled ? logStreamName : null
  });

  // Also log to console for immediate visibility
  console.log(`🚀 S3 Microservice started successfully!`);
  console.log(`📍 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🌐 Server running on 0.0.0.0:${PORT}`);
  console.log(`📋 Available endpoints:`);
  console.log(`  GET  /health`);
  console.log(`  POST /api/upload/:userId/:fileName`);
  console.log(`  GET  /api/download?s3Key=...&fileName=...`);
  console.log(`  POST /api/export/:type/:userId/:fileName (types: json, csv, xml, txt, pdf)`);
  console.log(`✅ PDF Export: UPDATED AND WORKING - html-pdf-node integration complete`);
  if (cloudWatchLogsEnabled) {
    console.log(`📊 CloudWatch Logs: Enabled (Group: ${logGroupName}, Stream: ${logStreamName})`);
  }

  if (isProduction) {
    console.log(`🔒 Production mode enabled`);
    console.log(`📊 Health check available at: http://0.0.0.0:${PORT}/health`);
  }

  // Send ready signal to PM2 if running under PM2
  if (process.send) {
    process.send('ready');
  }
});

// Handle server errors
server.on('error', (error) => {
  if (error.syscall !== 'listen') {
    throw error;
  }

  const bind = typeof PORT === 'string' ? 'Pipe ' + PORT : 'Port ' + PORT;

  switch (error.code) {
    case 'EACCES':
      console.error(`❌ ${bind} requires elevated privileges`);
      process.exit(1);
      break;
    case 'EADDRINUSE':
      console.error(`❌ ${bind} is already in use`);
      process.exit(1);
      break;
    default:
      throw error;
  }
});

// Set server timeouts for large file uploads
server.timeout = 600000; // 10 minutes
server.keepAliveTimeout = 65000; // 65 seconds
server.headersTimeout = 66000; // 66 seconds

// Graceful shutdown
process.on('SIGTERM', async () => {
  log.info('SIGTERM signal received: closing HTTP server');
  await logger.flush();
  server.close(() => {
    log.info('HTTP server closed');
    process.exit(0);
  });
});

process.on('SIGINT', async () => {
  log.info('SIGINT signal received: closing HTTP server');
  await logger.flush();
  server.close(() => {
    log.info('HTTP server closed');
    process.exit(0);
  });
});

module.exports = app;