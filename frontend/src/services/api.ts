import axios from 'axios';
import { authService } from './auth';

// Determine API URL. Prioritize VITE_API_BASE_URL.
// Fallback to relative path for same-origin proxy or direct to localhost:8000 for local dev.
let resolvedApiUrl = import.meta.env.VITE_API_BASE_URL;

if (!resolvedApiUrl) {
  // If VITE_API_BASE_URL is not set, behavior might differ for dev vs prod.
  // For dev, Vite proxy usually handles relative paths. For prod, Nginx handles it.
  // A common default if served on same domain (through proxy) is just the path.
  // If backend is on a different domain or port without proxy, full URL is needed.
  // The Vite dev server proxy targets localhost:8000 for /api.
  // The production Nginx proxies /api to backend:8000.
  // So, using "/api" as a base and then appending "/v1/..." in calls might be more consistent
  // OR ensure VITE_API_BASE_URL is always set appropriately.
  // For simplicity here, let's assume if not set, it's local dev wanting to hit backend directly
  // or it's a build where it should have been set (e.g. to '/').
  
  // If running in dev mode ( Vite specific import.meta.env.DEV ) and no env var,
  // we could default to something that works with the Vite proxy e.g. '',
  // so calls like axios.get('/api/v1/health') work.
  // Or, if we expect full paths like `http://localhost:8000/api/v1/health` for dev,
  // then `http://localhost:8000` is a sensible default if VITE_API_BASE_URL is missing.
  // The current .env.development provides VITE_API_BASE_URL=http://localhost:8000.

  // Let's keep it simple: if VITE_API_BASE_URL is not provided, default to http://localhost:8000.
  // This matches the previous hardcoded default and behavior of .env.development.
  resolvedApiUrl = 'http://localhost:8000';
  console.warn("VITE_API_BASE_URL is not set. Defaulting to http://localhost:8000.");
}

// Create axios instance
const api = axios.create({
  baseURL: resolvedApiUrl,
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
  
  // Note: If baseURL is 'http://localhost:8000', path should be '/api/v1/documents/upload'
  // If baseURL is 'http://localhost:8000/api/v1', path should be '/documents/upload'
  // The current .env files set VITE_API_BASE_URL to the host (e.g. http://localhost:8000)
  // and API calls in api.ts include /api/v1. This is consistent.
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
