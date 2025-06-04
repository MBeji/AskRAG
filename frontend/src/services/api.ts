import axios from 'axios';
import { authService } from './auth';

// Get API URL from environment or settings
const getApiUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl;
  
  const settings = localStorage.getItem('askrag-settings');
  if (settings) {
    const parsed = JSON.parse(settings);
    return parsed.apiUrl || 'http://localhost:8000';
  }
  return 'http://localhost:8000';
};

// Create axios instance
const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const tokens = authService.getStoredTokens();
    if (tokens?.accessToken) {
      config.headers.Authorization = `Bearer ${tokens.accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const tokens = authService.getStoredTokens();
        if (tokens?.refreshToken) {
          const newTokens = await authService.refreshToken(tokens.refreshToken);
          authService.storeTokens(newTokens);
          originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        authService.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Document operations
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocuments = async () => {
  const response = await api.get('/api/v1/documents');
  return response.data;
};

export const deleteDocument = async (documentId: string) => {
  const response = await api.delete(`/api/v1/documents/${documentId}`);
  return response.data;
};

// Chat operations
export const sendChatMessage = async (message: string, documentIds?: string[]) => {
  const response = await api.post('/api/v1/chat', {
    message,
    document_ids: documentIds,
  });
  return response.data;
};

export const getChatHistory = async () => {
  const response = await api.get('/api/v1/chat/history');
  return response.data;
};

// Settings operations
export const getSettings = async () => {
  const response = await api.get('/api/v1/settings');
  return response.data;
};

export const updateSettings = async (settings: any) => {
  const response = await api.put('/api/v1/settings', settings);
  return response.data;
};

export default api;
