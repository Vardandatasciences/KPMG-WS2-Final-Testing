'use strict';

/**
 * SSRF hardening for Atlassian Jira Cloud integration servers.
 * Validates dynamic path/query segments and attachment download URLs before axios/fetch.
 */

const ATLASSIAN_CLOUD_ID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function assertSafeAtlassianCloudId(id) {
  if (typeof id !== 'string' || !ATLASSIAN_CLOUD_ID_RE.test(id.trim())) {
    throw new Error('Invalid Atlassian cloud ID format');
  }
  return id.trim();
}

/**
 * Jira REST accepts numeric id or project key (e.g. PROJ, TEAM_1).
 */
function assertSafeJiraProjectId(projectId) {
  const s = String(projectId).trim();
  if (s.length < 1 || s.length > 32) {
    throw new Error('Invalid Jira project id length');
  }
  if (/^\d{1,20}$/.test(s)) {
    return s;
  }
  if (/^[A-Za-z][A-Za-z0-9_]*$/.test(s)) {
    return s;
  }
  throw new Error('Invalid Jira project id or key');
}

function assertSafeJiraAttachmentId(id) {
  const s = String(id).trim();
  if (!/^\d{1,20}$/.test(s)) {
    throw new Error('Invalid Jira attachment id');
  }
  return s;
}

/**
 * Attachment `content` from Jira metadata must stay under the same cloud instance on api.atlassian.com.
 */
function assertHttpsAtlassianAttachmentContentUrl(contentUrl, cloudId) {
  const cid = assertSafeAtlassianCloudId(cloudId);
  let u;
  try {
    u = new URL(contentUrl);
  } catch {
    throw new Error('Invalid attachment content URL');
  }
  if (u.protocol !== 'https:') {
    throw new Error('Attachment content must use HTTPS');
  }
  if (u.hostname.toLowerCase() !== 'api.atlassian.com') {
    throw new Error('Attachment content host not allowed');
  }
  const expected = `/ex/jira/${cid}/`;
  if (!u.pathname.startsWith(expected)) {
    throw new Error('Attachment URL path does not match cloud instance');
  }
}

function cloudIdAllowedForToken(cloudId, resources) {
  assertSafeAtlassianCloudId(cloudId);
  if (!Array.isArray(resources)) {
    throw new Error('Invalid accessible resources');
  }
  return resources.some((r) => r && r.id === cloudId);
}

module.exports = {
  assertSafeAtlassianCloudId,
  assertSafeJiraProjectId,
  assertSafeJiraAttachmentId,
  assertHttpsAtlassianAttachmentContentUrl,
  cloudIdAllowedForToken,
};
