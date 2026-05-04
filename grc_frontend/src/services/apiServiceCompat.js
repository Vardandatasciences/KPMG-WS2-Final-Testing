/**
 * Thin compatibility layer over `apiService` — same axios instance, interceptors, CSRF, and auth.
 * Incident module (and others) may import `axiosCompat` / `fetchCompat` / `incidentServiceCompat` here
 * instead of `apiService` directly; behavior is equivalent for transport security.
 * Prefer `apiService` in new code for clarity; use compat only to match legacy call shapes.
 */
import apiService from '@/services/apiService.js';
import { useFrameworkStore } from '@/stores/framework';

const buildConfig = (config = {}) => {
  const safeConfig = { ...config };
  delete safeConfig.params;
  return safeConfig;
};

export const axiosCompat = {
  async get(url, config = {}) {
    const data = await apiService.get(url, config.params || {}, buildConfig(config));
    return { data, status: 200 };
  },
  async post(url, body = {}, config = {}) {
    const data = await apiService.post(url, body, buildConfig(config));
    return { data, status: 200 };
  },
  async put(url, body = {}, config = {}) {
    const data = await apiService.put(url, body, buildConfig(config));
    return { data, status: 200 };
  },
  async patch(url, body = {}, config = {}) {
    const data = await apiService.patch(url, body, buildConfig(config));
    return { data, status: 200 };
  },
  async delete(url, config = {}) {
    const data = await apiService.delete(url, buildConfig(config));
    return { data, status: 200 };
  }
};

export const fetchCompat = async (url, options = {}) => {
  const method = (options.method || 'GET').toLowerCase();
  const headers = options.headers || {};
  const config = { headers };
  let parsedBody = options.body || {};
  if (typeof parsedBody === 'string') {
    try {
      parsedBody = JSON.parse(parsedBody);
    } catch (_) {
      parsedBody = { value: parsedBody };
    }
  }
  let data;

  if (method === 'get') {
    data = await apiService.get(url, {}, config);
  } else if (method === 'post') {
    data = await apiService.post(url, parsedBody, config);
  } else if (method === 'put') {
    data = await apiService.put(url, parsedBody, config);
  } else if (method === 'patch') {
    data = await apiService.patch(url, parsedBody, config);
  } else if (method === 'delete') {
    data = await apiService.delete(url, config);
  } else {
    throw new Error(`Unsupported method: ${method}`);
  }

  return {
    ok: true,
    status: 200,
    async json() {
      return data;
    },
    async text() {
      return JSON.stringify(data);
    }
  };
};

export const incidentServiceCompat = {
  getIncidentDashboard: async (params = {}) => {
    const data = await apiService.get('/api/incidents/dashboard/', params);
    return { data, status: 200 };
  },
  getIncidentAnalytics: async (body = {}) => {
    const data = await apiService.post('/api/incidents/dashboard/analytics/', body);
    return { data, status: 200 };
  },
  getRecentIncidents: async (limit = 3) => {
    const data = await apiService.get('/api/incidents/recent/', { limit });
    return { data, status: 200 };
  },
  getIncidentFrameworks: async () => {
    const data = await apiService.get('/api/compliance/frameworks/public/');
    return { data, status: 200 };
  },
  getSelectedFramework: async () => {
    const frameworkStore = useFrameworkStore();
    await frameworkStore.loadFrameworkFromSession();
    const data = {
      success: true,
      frameworkId: frameworkStore.selectedFrameworkId,
      frameworkName: frameworkStore.selectedFrameworkName,
    };
    return { data, status: 200 };
  }
};

