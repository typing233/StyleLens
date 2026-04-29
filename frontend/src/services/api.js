import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const cssAnalyzerApi = {
  analyzeUrl: async (url, options = {}) => {
    const response = await api.post('/analyze', {
      url,
      options: {
        include_inline: true,
        include_external: true,
        deep_analysis: true,
        ...options
      }
    });
    return response.data;
  },

  getAnalysis: async (analysisId) => {
    const response = await api.get(`/analysis/${analysisId}`);
    return response.data;
  },

  deleteAnalysis: async (analysisId) => {
    const response = await api.delete(`/analysis/${analysisId}`);
    return response.data;
  },

  exportReport: async (analysisId, format = 'html') => {
    const response = await api.post('/report/export', {
      analysis_id: analysisId,
      format,
      include_visualization: true
    });
    return response.data;
  },

  llmAnalyze: async (analysisId, customPrompt = null) => {
    const params = { analysis_id: analysisId };
    if (customPrompt) {
      params.custom_prompt = customPrompt;
    }
    const response = await api.post('/llm/analyze', null, { params });
    return response.data;
  },

  llmRefactor: async (analysisId) => {
    const response = await api.post('/llm/refactor', null, {
      params: { analysis_id: analysisId }
    });
    return response.data;
  }
};

export const llmConfigApi = {
  configure: async (config) => {
    const response = await api.post('/llm/configure', config);
    return response.data;
  },

  testConnection: async (config) => {
    const response = await api.post('/llm/test', config);
    return response.data;
  },

  getConfig: async () => {
    const response = await api.get('/llm/config');
    return response.data;
  },

  getStatus: async () => {
    const response = await api.get('/llm/status');
    return response.data;
  },

  clearConfig: async () => {
    const response = await api.delete('/llm/config');
    return response.data;
  }
};

export default api;
