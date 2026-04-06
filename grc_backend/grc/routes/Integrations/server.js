const express = require('express');
const axios = require('axios');
const querystring = require('querystring');
const path = require('path');
const cors = require('cors');
const {
  assertSafeAtlassianCloudId,
  assertSafeJiraProjectId,
} = require('./atlassian_ssrf_guard');

try {
  require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '..', '.env') });
} catch (_) {
  /* dotenv optional */
}

const app = express();
const isProd = process.env.NODE_ENV === 'production';
const port = parseInt(process.env.JIRA_DEV_PORT || process.env.PORT || '5000', 10);

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

app.get('/oauth', (req, res) => {
  const authUrlWithParams = `${authUrl}?${querystring.stringify({
    client_id: clientId,
    scope: 'read:jira-user read:jira-work',
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

// Fetch Jira projects
app.get('/jira-projects', async (req, res) => {
  const { token } = req.query;
  
  if (!token) {
    return res.status(400).json({ error: 'No access token provided' });
  }

  console.log('Fetching projects with token:', token.substring(0, 20) + '...');

  try {
    // First, let's try to get the cloud ID by calling the accessible resources endpoint
    console.log('🔍 Making request to accessible resources endpoint...');
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
      var cloudId = resourcesResponse.data[0].id;
      var resourceName = resourcesResponse.data[0].name;
    } else {
      console.log('✅ Found Jira resources:', jiraResources.length);
      var cloudId = jiraResources[0].id;
      var resourceName = jiraResources[0].name;
    }

    console.log('🔍 Using cloud ID:', cloudId);
    console.log('🔍 Resource name:', resourceName);

    if (!cloudId) {
      return res.status(400).json({ error: 'Cloud ID not found in accessible resources' });
    }

    try {
      assertSafeAtlassianCloudId(cloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }

    // Test connection first with myself endpoint
    console.log('🔍 Testing connection with myself endpoint...');
    const myselfResponse = await axios.get(`https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/myself`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    });

    console.log('✅ Connection test successful:', myselfResponse.data.displayName);

    // Fetch projects using the access token and cloud ID
    console.log('🔍 Fetching projects...');
    const response = await axios.get(`https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/project`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    });

    console.log('✅ Projects response:', response.data.length, 'projects found');
    res.json({ projects: response.data });
  } catch (error) {
    console.error('❌ Error fetching Jira projects:');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error response status:', error.response?.status);
    console.error('Error response data:', error.response?.data);
    res.status(500).json({ error: 'Error fetching Jira projects', details: error.response?.data || error.message });
  }
});

// Fetch detailed project information
app.get('/jira-project-details', async (req, res) => {
  const { token, projectId } = req.query;
  
  console.log('🔍 Project details request received:');
  console.log('🔍 Token:', token ? token.substring(0, 20) + '...' : 'No token');
  console.log('🔍 Project ID:', projectId);
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

  try {
    // Get accessible resources to find cloud ID
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

    const cloudId = jiraResources.length > 0 ? jiraResources[0].id : resourcesResponse.data[0].id;

    try {
      assertSafeAtlassianCloudId(cloudId);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid cloud ID from provider', details: e.message });
    }

    // Fetch detailed project information
    const projectResponse = await axios.get(
      `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/project/${encodeURIComponent(safeProjectId)}`,
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
        `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/project/${encodeURIComponent(safeProjectId)}/components`,
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
        `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/project/${encodeURIComponent(safeProjectId)}/versions`,
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

    // Fetch project issues (first 50) - try with project ID first, then project key
    let issuesResponse;
    try {
      const jqlPrimary = `project=${safeProjectId}`;
      issuesResponse = await axios.get(
        `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/search?jql=${encodeURIComponent(jqlPrimary)}&maxResults=50`,
        {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
      });
    } catch (issueError) {
      console.log('⚠️ Failed to fetch issues with project ID, trying with project key...');
      try {
        // Try with project key instead
        const key = assertSafeJiraProjectId(projectResponse.data.key);
        const jqlKey = `project="${key}"`;
        issuesResponse = await axios.get(
          `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/search?jql=${encodeURIComponent(jqlKey)}&maxResults=50`,
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

    const projectDetails = {
      project: projectResponse.data,
      components: componentsResponse.data,
      versions: versionsResponse.data,
      issues: issuesResponse.data
    };

    console.log('✅ Project details fetched successfully');
    res.json(projectDetails);
  } catch (error) {
    console.error('❌ Error fetching project details:');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error response status:', error.response?.status);
    console.error('Error response data:', error.response?.data);
    res.status(500).json({ error: 'Error fetching project details', details: error.response?.data || error.message });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
