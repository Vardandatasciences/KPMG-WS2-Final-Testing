const express = require('express');
const axios = require('axios');
const querystring = require('querystring');
const path = require('path');
const cors = require('cors');
const {
  assertSafeAtlassianCloudId,
  assertSafeJiraProjectId,
  assertSafeJiraAttachmentId,
  assertHttpsAtlassianAttachmentContentUrl,
  cloudIdAllowedForToken,
} = require('./atlassian_ssrf_guard');

try {
  require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '..', '.env') });
} catch (_) {
  /* optional */
}

const app = express();
const isProd = process.env.NODE_ENV === 'production';
const port = parseInt(process.env.JIRA_DEV_PORT || process.env.PORT || '5000', 10);
const publicBase = (
  process.env.JIRA_PUBLIC_BASE_URL || `http://127.0.0.1:${port}`
).replace(/\/$/, '');

const defaultDevOrigins = [
  'http://localhost:8080',
  'http://127.0.0.1:8080',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
  'https://grc-tprm.vardaands.com',
  'https://riskavaire.vardaands.com',
  'https://test-riskavaire.vardaands.com',
];
const envOrigins = (process.env.JIRA_CORS_ORIGINS || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);
const allowedOrigins = envOrigins.length ? envOrigins : defaultDevOrigins;
if (isProd && envOrigins.length === 0) {
  console.warn('[JIRA server] Set JIRA_CORS_ORIGINS in production for an explicit allowlist.');
}

app.use(cors({
  origin(origin, callback) {
    // Allow non-browser clients/tools that do not send Origin.
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin)) return callback(null, true);
    return callback(new Error('CORS origin not allowed'), false);
  },
  credentials: false,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
}));
app.use(express.json());

const clientId = (process.env.JIRA_OAUTH_CLIENT_ID || '').trim();
const clientSecret = (process.env.JIRA_OAUTH_CLIENT_SECRET || '').trim();
const redirectUri =
  (process.env.JIRA_OAUTH_REDIRECT_URI || `http://127.0.0.1:${port}/oauth/callback`).trim();
const oauthSuccessRedirect =
  (process.env.JIRA_OAUTH_SUCCESS_REDIRECT || 'http://localhost:8080/integration/jira?success=true').trim();
const authUrl = 'https://auth.atlassian.com/authorize';
const tokenUrl = 'https://auth.atlassian.com/oauth/token';

if (isProd && (!clientId || !clientSecret)) {
  throw new Error(
    'Production requires JIRA_OAUTH_CLIENT_ID and JIRA_OAUTH_CLIENT_SECRET (no embedded credentials).'
  );
}
if (!isProd && (!clientId || !clientSecret)) {
  console.warn('[JIRA server] Set JIRA_OAUTH_CLIENT_ID / JIRA_OAUTH_CLIENT_SECRET for OAuth.');
}

let accessToken = null;

function getRequestToken(req) {
  // Prefer server-side stored OAuth token; keep query token as legacy fallback.
  return accessToken || req.query.token;
}

// Function to validate token by testing it against Atlassian API
async function validateToken(token) {
  try {
    const response = await axios.get('https://api.atlassian.com/oauth/token/accessible-resources', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
      timeout: 10000
    });
    return { valid: true, resources: response.data };
  } catch (error) {
    console.log('🔍 Token validation failed:', error.response?.status, error.message);
    return { valid: false, error: error.response?.data || error.message };
  }
}

// Enhanced error handler for API responses
function handleApiError(error, context) {
  const status = error.response?.status;
  const data = error.response?.data;
  
  console.error(`❌ ${context} error:`, {
    status,
    message: error.message,
    data: data
  });
  
  if (status === 401) {
    return { error: 'Authentication failed. Token may be expired or invalid.', status: 401, shouldReauth: true };
  } else if (status === 403) {
    return { error: 'Access forbidden. Check permissions and scopes.', status: 403 };
  } else if (status === 404) {
    return { error: 'Resource not found.', status: 404 };
  } else if (status === 410) {
    return { error: 'Resource no longer available.', status: 410 };
  } else {
    return { error: `API error: ${error.message}`, status: status || 500, details: data };
  }
}

app.get('/oauth', (req, res) => {
  const authUrlWithParams = `${authUrl}?${querystring.stringify({
    client_id: clientId,
    scope: 'read:jira-user read:jira-work read:jira-project offline_access',
    response_type: 'code',
    redirect_uri: redirectUri,
  })}`;
  res.redirect(authUrlWithParams);
});

app.get('/oauth/callback', async (req, res) => {
  const { code } = req.query;

  try {
    // Step 2: Exchange the code for an access token
    const response = await axios.post(tokenUrl, querystring.stringify({
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: redirectUri,
      client_id: clientId,
      client_secret: clientSecret,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Store the access token server-side; never put OAuth tokens in URL query params.
    accessToken = response.data.access_token;
    res.redirect(oauthSuccessRedirect);
  } catch (error) {
    res.status(500).send('Error during OAuth flow');
  }
});

// Get accessible Jira resources for account selection
app.get('/jira-resources', async (req, res) => {
  const { token } = req.query;
  
  if (!token) {
    return res.status(400).json({ error: 'No access token provided' });
  }

  console.log('🔍 Fetching accessible resources with token:', token.substring(0, 20) + '...');

  // Validate token first
  const validation = await validateToken(token);
  if (!validation.valid) {
    const errorResponse = handleApiError({ response: { status: 401, data: validation.error } }, 'Token validation');
    return res.status(errorResponse.status).json(errorResponse);
  }

  try {
    console.log('✅ Token validated successfully');
    const resourcesResponse = validation.resources;

    console.log('🔍 Accessible resources count:', resourcesResponse.length);

    if (!resourcesResponse || resourcesResponse.length === 0) {
      return res.status(400).json({ error: 'No accessible Jira resources found' });
    }

    // Filter for Jira resources only
    const jiraResources = resourcesResponse.filter(resource => 
      resource.name && (
        resource.name.toLowerCase().includes('jira') ||
        resource.scopes.some(scope => scope.includes('jira'))
      )
    );

    // If no Jira resources found, return all resources
    const resourcesToReturn = jiraResources.length > 0 ? jiraResources : resourcesResponse;

    console.log('✅ Returning resources for selection:', resourcesToReturn.length);
    console.log('🔍 Resource details:', resourcesToReturn.map(r => ({ id: r.id, name: r.name, scopes: r.scopes })));
    
    res.json({ 
      resources: resourcesToReturn,
      hasMultipleAccounts: resourcesToReturn.length > 1,
      tokenValid: true
    });
  } catch (error) {
    const errorResponse = handleApiError(error, 'Fetching accessible resources');
    res.status(errorResponse.status).json(errorResponse);
  }
});

// Fetch Jira projects
app.get('/jira-projects', async (req, res) => {
  const { token, cloudId } = req.query;
  
  if (!token) {
    return res.status(400).json({ error: 'No access token provided' });
  }

  console.log('🔍 Fetching projects with token:', token.substring(0, 20) + '...');
  console.log('🔍 Using cloudId:', cloudId || 'auto-select');

  // Validate token first
  const validation = await validateToken(token);
  if (!validation.valid) {
    const errorResponse = handleApiError({ response: { status: 401, data: validation.error } }, 'Token validation');
    return res.status(errorResponse.status).json(errorResponse);
  }

  try {
    let selectedCloudId = cloudId;
    let resourceName = 'Unknown';

    // If cloudId is provided, use it directly (must match OAuth accessible resources).
    if (cloudId) {
      console.log('🔍 Using provided cloud ID:', cloudId);
      try {
        assertSafeAtlassianCloudId(cloudId);
        if (!cloudIdAllowedForToken(cloudId, validation.resources)) {
          return res.status(403).json({ error: 'Cloud ID is not authorized for this token' });
        }
      } catch (e) {
        return res.status(400).json({ error: 'Invalid cloud ID', details: e.message });
      }
      selectedCloudId = cloudId;

      // Get resource name by fetching accessible resources
      try {
        const resourcesResponse = await axios.get('https://api.atlassian.com/oauth/token/accessible-resources', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json',
          },
        });
        
        const resource = resourcesResponse.data.find(r => r.id === cloudId);
        if (resource) {
          resourceName = resource.name;
        }
      } catch (error) {
        console.log('⚠️ Could not fetch resource name for cloudId:', cloudId);
      }
    } else {
      // Auto-select logic (fallback for backward compatibility)
      console.log('🔍 Auto-selecting cloud ID...');
      const resourcesResponse = await axios.get('https://api.atlassian.com/oauth/token/accessible-resources', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
      });

      console.log('🔍 Resources response status:', resourcesResponse.status);
      console.log('🔍 Accessible resources:', JSON.stringify(resourcesResponse.data, null, 2));

      if (!resourcesResponse.data || resourcesResponse.data.length === 0) {
        return res.status(400).json({ error: 'No accessible Jira resources found' });
      }

      // Filter for Jira resources only
      const jiraResources = resourcesResponse.data.filter(resource => 
        resource.name && resource.name.toLowerCase().includes('jira')
      );

      if (jiraResources.length === 0) {
        console.log('⚠️ No Jira resources found, using first available resource');
        selectedCloudId = resourcesResponse.data[0].id;
        resourceName = resourcesResponse.data[0].name;
      } else {
        console.log('✅ Found Jira resources:', jiraResources.length);
        selectedCloudId = jiraResources[0].id;
        resourceName = jiraResources[0].name;
      }
    }

    console.log('🔍 Final cloud ID:', selectedCloudId);
    console.log('🔍 Resource name:', resourceName);

    if (!selectedCloudId) {
      return res.status(400).json({ error: 'Cloud ID not found in accessible resources' });
    }

    try {
      assertSafeAtlassianCloudId(selectedCloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }

    // Test connection first with myself endpoint
    console.log('🔍 Testing connection with myself endpoint...');
    const myselfResponse = await axios.get(`https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/myself`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    });

    console.log('✅ Connection test successful:', myselfResponse.data.displayName);

    // Fetch projects using the access token and cloud ID
    console.log('🔍 Fetching projects...');
    const response = await axios.get(`https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/project`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    });

    console.log('✅ Projects response:', response.data.length, 'projects found');
    res.json({ 
      projects: response.data,
      cloudId: selectedCloudId,
      resourceName: resourceName
    });
  } catch (error) {
    const errorResponse = handleApiError(error, 'Fetching Jira projects');
    res.status(errorResponse.status).json(errorResponse);
  }
});

// Fetch detailed project information
app.get('/jira-project-details', async (req, res) => {
  const { token, projectId, cloudId } = req.query;
  
  console.log('🔍 Project details request received:');
  console.log('🔍 Token:', token ? token.substring(0, 20) + '...' : 'No token');
  console.log('🔍 Project ID:', projectId);
  console.log('🔍 Cloud ID:', cloudId || 'auto-select');
  console.log('🔍 Full query params:', req.query);
  
  if (!token) {
    console.log('❌ No access token provided');
    return res.status(400).json({ error: 'No access token provided' });
  }
  
  if (!projectId) {
    console.log('❌ No project ID provided');
    return res.status(400).json({ error: 'No project ID provided' });
  }

  let safeProjectId;
  try {
    safeProjectId = assertSafeJiraProjectId(projectId);
  } catch (e) {
    return res.status(400).json({ error: 'Invalid project id or key', details: e.message });
  }

  console.log('✅ Fetching project details for project ID:', safeProjectId);

  // Validate token first
  const validation = await validateToken(token);
  if (!validation.valid) {
    const errorResponse = handleApiError({ response: { status: 401, data: validation.error } }, 'Token validation');
    return res.status(errorResponse.status).json(errorResponse);
  }

  try {
    let selectedCloudId = cloudId;

    if (cloudId) {
      try {
        assertSafeAtlassianCloudId(cloudId);
        if (!cloudIdAllowedForToken(cloudId, validation.resources)) {
          return res.status(403).json({ error: 'Cloud ID is not authorized for this token' });
        }
      } catch (e) {
        return res.status(400).json({ error: 'Invalid cloud ID', details: e.message });
      }
    }

    // If cloudId is not provided, auto-select
    if (!cloudId) {
      console.log('🔍 Auto-selecting cloud ID for project details...');
      const resourcesResponse = await axios.get('https://api.atlassian.com/oauth/token/accessible-resources', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
      });

      if (!resourcesResponse.data || resourcesResponse.data.length === 0) {
        return res.status(400).json({ error: 'No accessible Jira resources found' });
      }

      // Filter for Jira resources
      const jiraResources = resourcesResponse.data.filter(resource => 
        resource.name && resource.name.toLowerCase().includes('jira')
      );

      selectedCloudId = jiraResources.length > 0 ? jiraResources[0].id : resourcesResponse.data[0].id;
    }

    try {
      assertSafeAtlassianCloudId(selectedCloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }
    
    console.log('🔍 Using cloud ID for project details:', selectedCloudId);

    // Fetch detailed project information
    const projectResponse = await axios.get(
      `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/project/${encodeURIComponent(safeProjectId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
      }
    );

    // Fetch project components
    let componentsResponse;
    try {
      componentsResponse = await axios.get(
        `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/project/${encodeURIComponent(safeProjectId)}/components`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'application/json',
          },
        }
      );
    } catch (componentError) {
      console.log('⚠️ Failed to fetch components:', componentError.message);
      componentsResponse = { data: [] };
    }

    // Fetch project versions
    let versionsResponse;
    try {
      versionsResponse = await axios.get(
        `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/project/${encodeURIComponent(safeProjectId)}/versions`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'application/json',
          },
        }
      );
    } catch (versionError) {
      console.log('⚠️ Failed to fetch versions:', versionError.message);
      versionsResponse = { data: [] };
    }

    // Fetch project issues (first 50) with attachments - try with project ID first, then project key
    let issuesResponse;
    try {
      const jqlIssues = `project=${safeProjectId}`;
      issuesResponse = await axios.get(
        `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/search?jql=${encodeURIComponent(jqlIssues)}&expand=attachment&fields=*all&maxResults=50`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'application/json',
          },
        }
      );
    } catch (issueError) {
      console.log('⚠️ Failed to fetch issues with project ID, trying with project key...');
      try {
        const key = assertSafeJiraProjectId(projectResponse.data.key);
        const jqlKey = `project="${key}"`;
        issuesResponse = await axios.get(
          `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/search?jql=${encodeURIComponent(jqlKey)}&expand=attachment&fields=*all&maxResults=50`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              Accept: 'application/json',
            },
          }
        );
      } catch (keyError) {
        console.log('⚠️ Failed to fetch issues with project key:', keyError.message);
        issuesResponse = { data: { issues: [], total: 0 } };
      }
    }

    // Fetch issues specifically with attachments
    let issuesWithAttachmentsResponse;
    try {
      const attachmentJQL = `project=${safeProjectId} AND attachments IS NOT EMPTY`;
      issuesWithAttachmentsResponse = await axios.get(`https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/search?jql=${encodeURIComponent(attachmentJQL)}&expand=attachment&fields=*all&maxResults=100`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
      });
    } catch (attachmentError) {
      console.log('⚠️ Failed to fetch issues with attachments, trying with project key...');
      try {
        const k = assertSafeJiraProjectId(projectResponse.data.key);
        const attachmentJQLKey = `project="${k}" AND attachments IS NOT EMPTY`;
        issuesWithAttachmentsResponse = await axios.get(`https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/search?jql=${encodeURIComponent(attachmentJQLKey)}&expand=attachment&fields=*all&maxResults=100`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json',
          },
        });
      } catch (keyAttachmentError) {
        console.log('⚠️ Failed to fetch issues with attachments using project key:', keyAttachmentError.message);
        issuesWithAttachmentsResponse = { data: { issues: [], total: 0 } };
      }
    }

    // Extract all attachments from issues
    const allAttachments = [];
    if (issuesWithAttachmentsResponse.data.issues) {
      issuesWithAttachmentsResponse.data.issues.forEach(issue => {
        if (issue.fields && issue.fields.attachment) {
          issue.fields.attachment.forEach(attachment => {
            allAttachments.push({
              id: attachment.id,
              filename: attachment.filename,
              size: attachment.size,
              mimeType: attachment.mimeType,
              content: attachment.content,
              thumbnail: attachment.thumbnail,
              author: attachment.author,
              created: attachment.created,
              issueKey: issue.key,
              issueId: issue.id,
              issueSummary: issue.fields.summary
            });
          });
        }
      });
    }

    console.log(`✅ Found ${allAttachments.length} attachments across ${issuesWithAttachmentsResponse.data.issues?.length || 0} issues with attachments`);

    const projectDetails = {
      project: projectResponse.data,
      components: componentsResponse.data,
      versions: versionsResponse.data,
      issues: issuesResponse.data,
      issuesWithAttachments: issuesWithAttachmentsResponse.data,
      attachments: allAttachments,
      attachmentSummary: {
        totalAttachments: allAttachments.length,
        totalIssuesWithAttachments: issuesWithAttachmentsResponse.data.issues?.length || 0,
        attachmentTypes: [...new Set(allAttachments.map(att => att.mimeType))],
        totalSize: allAttachments.reduce((sum, att) => sum + (att.size || 0), 0)
      }
    };

    console.log('✅ Project details fetched successfully');
    res.json({
      ...projectDetails,
      cloudId: selectedCloudId,
      tokenValid: true
    });
  } catch (error) {
    const errorResponse = handleApiError(error, 'Fetching project details');
    res.status(errorResponse.status).json(errorResponse);
  }
});

// Debug endpoint to check token status
app.get('/debug-token', async (req, res) => {
  const { token } = req.query;
  
  if (!token) {
    return res.status(400).json({ error: 'No access token provided' });
  }

  console.log('🔍 Debug token request for token:', token.substring(0, 20) + '...');

  try {
    const validation = await validateToken(token);
    
    if (validation.valid) {
      const resources = validation.resources;
      const jiraResources = resources.filter(resource => 
        resource.name && (
          resource.name.toLowerCase().includes('jira') ||
          resource.scopes.some(scope => scope.includes('jira'))
        )
      );

      res.json({
        tokenValid: true,
        totalResources: resources.length,
        jiraResources: jiraResources.length,
        resources: resources.map(r => ({
          id: r.id,
          name: r.name,
          scopes: r.scopes,
          avatarUrl: r.avatarUrl
        })),
        jiraResourcesDetails: jiraResources.map(r => ({
          id: r.id,
          name: r.name,
          scopes: r.scopes
        }))
      });
    } else {
      res.status(401).json({
        tokenValid: false,
        error: validation.error,
        suggestion: 'Token may be expired or invalid. Try re-authenticating.'
      });
    }
  } catch (error) {
    const errorResponse = handleApiError(error, 'Token debug');
    res.status(errorResponse.status).json(errorResponse);
  }
});

// List all attachments for a project (simplified endpoint)
app.get('/jira-attachments-list', async (req, res) => {
  const { token, projectId, cloudId } = req.query;
  
  if (!token) {
    return res.status(400).json({ error: 'No access token provided' });
  }
  
  if (!projectId) {
    return res.status(400).json({ error: 'No project ID provided' });
  }

  let safeProjectIdList;
  try {
    safeProjectIdList = assertSafeJiraProjectId(projectId);
  } catch (e) {
    return res.status(400).json({ error: 'Invalid project id or key', details: e.message });
  }

  console.log('🔍 Fetching attachments list for project:', safeProjectIdList);

  // Validate token first
  const validation = await validateToken(token);
  if (!validation.valid) {
    const errorResponse = handleApiError({ response: { status: 401, data: validation.error } }, 'Token validation');
    return res.status(errorResponse.status).json(errorResponse);
  }

  try {
    let selectedCloudId = cloudId;

    if (cloudId) {
      try {
        assertSafeAtlassianCloudId(cloudId);
        if (!cloudIdAllowedForToken(cloudId, validation.resources)) {
          return res.status(403).json({ error: 'Cloud ID is not authorized for this token' });
        }
      } catch (e) {
        return res.status(400).json({ error: 'Invalid cloud ID', details: e.message });
      }
    }
    
    // Auto-select cloudId if not provided
    if (!cloudId) {
      const jiraResources = validation.resources.filter(resource => 
        resource.name && resource.name.toLowerCase().includes('jira')
      );
      selectedCloudId = jiraResources.length > 0 ? jiraResources[0].id : validation.resources[0].id;
    }

    try {
      assertSafeAtlassianCloudId(selectedCloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }

    // Search for issues with attachments
    const attachmentJQL = `project=${safeProjectIdList} AND attachments IS NOT EMPTY`;
    const issuesResponse = await axios.get(`https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/search?jql=${encodeURIComponent(attachmentJQL)}&expand=attachment&fields=attachment,summary,key&maxResults=100`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    });

    // Extract and format attachments
    const attachmentsList = [];
    if (issuesResponse.data.issues) {
      issuesResponse.data.issues.forEach(issue => {
        if (issue.fields && issue.fields.attachment) {
          issue.fields.attachment.forEach(attachment => {
            let aid;
            try {
              aid = assertSafeJiraAttachmentId(String(attachment.id));
            } catch {
              return;
            }
            attachmentsList.push({
              attachmentId: aid,
              filename: attachment.filename,
              size: attachment.size,
              sizeFormatted: formatFileSize(attachment.size),
              mimeType: attachment.mimeType,
              fileType: getFileType(attachment.filename),
              created: attachment.created,
              author: attachment.author?.displayName || 'Unknown',
              issueKey: issue.key,
              issueSummary: issue.fields.summary,
              downloadUrl: `${publicBase}/jira-attachment/${encodeURIComponent(aid)}?cloudId=${encodeURIComponent(selectedCloudId)}`,
              viewUrl: attachment.content,
              thumbnailUrl: attachment.thumbnail
            });
          });
        }
      });
    }

    console.log(`✅ Found ${attachmentsList.length} attachments in project ${safeProjectIdList}`);

    res.json({
      projectId: safeProjectIdList,
      cloudId: selectedCloudId,
      totalAttachments: attachmentsList.length,
      attachments: attachmentsList,
      attachmentTypes: [...new Set(attachmentsList.map(att => att.fileType))],
      totalSize: attachmentsList.reduce((sum, att) => sum + (att.size || 0), 0),
      totalSizeFormatted: formatFileSize(attachmentsList.reduce((sum, att) => sum + (att.size || 0), 0))
    });

  } catch (error) {
    const errorResponse = handleApiError(error, 'Fetching attachments list');
    res.status(errorResponse.status).json(errorResponse);
  }
});

// Helper function to format file sizes
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Helper function to get file type from filename
function getFileType(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const typeMap = {
    'pdf': 'PDF Document',
    'doc': 'Word Document',
    'docx': 'Word Document',
    'xls': 'Excel Spreadsheet',
    'xlsx': 'Excel Spreadsheet',
    'ppt': 'PowerPoint',
    'pptx': 'PowerPoint',
    'txt': 'Text File',
    'png': 'Image',
    'jpg': 'Image',
    'jpeg': 'Image',
    'gif': 'Image',
    'zip': 'Archive',
    'rar': 'Archive'
  };
  return typeMap[ext] || 'Unknown';
}

// Download/proxy JIRA attachment content
app.get('/jira-attachment/:attachmentId', async (req, res) => {
  const { cloudId } = req.query;
  const { attachmentId } = req.params;
  const token = getRequestToken(req);
  
  console.log('🔍 Attachment download request received:');
  console.log('🔍 Token:', token ? token.substring(0, 20) + '...' : 'No token');
  console.log('🔍 Attachment ID:', attachmentId);
  console.log('🔍 Cloud ID:', cloudId || 'auto-select');
  
  if (!token) {
    console.log('❌ No access token provided');
    return res.status(400).json({ error: 'No access token provided' });
  }
  
  if (!attachmentId) {
    console.log('❌ No attachment ID provided');
    return res.status(400).json({ error: 'No attachment ID provided' });
  }

  let safeAttId;
  try {
    safeAttId = assertSafeJiraAttachmentId(attachmentId);
  } catch (e) {
    return res.status(400).json({ error: 'Invalid attachment id', details: e.message });
  }

  const validation = await validateToken(token);
  if (!validation.valid) {
    const errorResponse = handleApiError({ response: { status: 401, data: validation.error } }, 'Token validation');
    return res.status(errorResponse.status).json(errorResponse);
  }

  try {
    let selectedCloudId = cloudId;

    if (cloudId) {
      try {
        assertSafeAtlassianCloudId(cloudId);
        if (!cloudIdAllowedForToken(cloudId, validation.resources)) {
          return res.status(403).json({ error: 'Cloud ID is not authorized for this token' });
        }
      } catch (e) {
        return res.status(400).json({ error: 'Invalid cloud ID', details: e.message });
      }
    } else {
      console.log('🔍 Auto-selecting cloud ID for attachment download...');
      const jiraResources = validation.resources.filter(resource => 
        resource.name && resource.name.toLowerCase().includes('jira')
      );
      if (!validation.resources || validation.resources.length === 0) {
        return res.status(400).json({ error: 'No accessible Jira resources found' });
      }
      selectedCloudId = jiraResources.length > 0 ? jiraResources[0].id : validation.resources[0].id;
    }
    
    console.log('🔍 Using cloud ID for attachment download:', selectedCloudId);

    try {
      assertSafeAtlassianCloudId(selectedCloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }

    // Get attachment metadata first
    const attachmentMetaResponse = await axios.get(
      `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/attachment/${safeAttId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
      }
    );

    const attachmentMeta = attachmentMetaResponse.data;
    console.log('✅ Attachment metadata:', attachmentMeta.filename, attachmentMeta.mimeType);

    try {
      assertHttpsAtlassianAttachmentContentUrl(attachmentMeta.content, selectedCloudId);
    } catch (e) {
      console.error('Blocked attachment content URL:', e.message);
      return res.status(400).json({ error: 'Refusing to fetch attachment from disallowed URL', details: e.message });
    }

    // Download the actual attachment content
    const attachmentResponse = await axios.get(attachmentMeta.content, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      responseType: 'stream'
    });

    // Set appropriate headers for the response
    res.set({
      'Content-Type': attachmentMeta.mimeType || 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${attachmentMeta.filename}"`,
      'Content-Length': attachmentMeta.size
    });

    // Pipe the attachment content to the response
    attachmentResponse.data.pipe(res);

    console.log('✅ Attachment downloaded successfully:', attachmentMeta.filename);
  } catch (error) {
    console.error('❌ Error downloading attachment:');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error response status:', error.response?.status);
    console.error('Error response data:', error.response?.data);
    res.status(500).json({ error: 'Error downloading attachment', details: error.response?.data || error.message });
  }
});

// Get attachment metadata without downloading content
app.get('/jira-attachment-meta', async (req, res) => {
  const { token, attachmentId, cloudId } = req.query;
  
  console.log('🔍 Attachment metadata request received:');
  console.log('🔍 Token:', token ? token.substring(0, 20) + '...' : 'No token');
  console.log('🔍 Attachment ID:', attachmentId);
  console.log('🔍 Cloud ID:', cloudId || 'auto-select');
  
  if (!token) {
    return res.status(400).json({ error: 'No access token provided' });
  }
  
  if (!attachmentId) {
    return res.status(400).json({ error: 'No attachment ID provided' });
  }

  let safeAttMetaId;
  try {
    safeAttMetaId = assertSafeJiraAttachmentId(attachmentId);
  } catch (e) {
    return res.status(400).json({ error: 'Invalid attachment id', details: e.message });
  }

  const validationMeta = await validateToken(token);
  if (!validationMeta.valid) {
    const errorResponse = handleApiError({ response: { status: 401, data: validationMeta.error } }, 'Token validation');
    return res.status(errorResponse.status).json(errorResponse);
  }

  try {
    let selectedCloudId = cloudId;

    if (cloudId) {
      try {
        assertSafeAtlassianCloudId(cloudId);
        if (!cloudIdAllowedForToken(cloudId, validationMeta.resources)) {
          return res.status(403).json({ error: 'Cloud ID is not authorized for this token' });
        }
      } catch (e) {
        return res.status(400).json({ error: 'Invalid cloud ID', details: e.message });
      }
    } else {
      const jiraResources = validationMeta.resources.filter(resource => 
        resource.name && resource.name.toLowerCase().includes('jira')
      );
      if (!validationMeta.resources || validationMeta.resources.length === 0) {
        return res.status(400).json({ error: 'No accessible Jira resources found' });
      }
      selectedCloudId = jiraResources.length > 0 ? jiraResources[0].id : validationMeta.resources[0].id;
    }

    try {
      assertSafeAtlassianCloudId(selectedCloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }

    // Get attachment metadata
    const attachmentResponse = await axios.get(
      `https://api.atlassian.com/ex/jira/${selectedCloudId}/rest/api/3/attachment/${safeAttMetaId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
      }
    );

    console.log('✅ Attachment metadata fetched successfully:', attachmentResponse.data.filename);
    res.json(attachmentResponse.data);
  } catch (error) {
    console.error('❌ Error fetching attachment metadata:');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error response status:', error.response?.status);
    console.error('Error response data:', error.response?.data);
    res.status(500).json({ error: 'Error fetching attachment metadata', details: error.response?.data || error.message });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});