// Document types
export interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  status: 'processing' | 'completed' | 'error';
  metadata?: {
    pages?: number;
    wordCount?: number;
    language?: string;
  };
}

// Authentication types
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'USER' | 'ADMIN' | 'SUPERUSER';
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  token: string;
  newPassword: string;
}

// Chat types
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: DocumentSource[];
}

export interface DocumentSource {
  documentId: string;
  documentName: string;
  chunk: string;
  similarity: number;
  page?: number;
}

export interface ChatResponse {
  message: ChatMessage;
  sources: DocumentSource[];
  processingTime: number;
}

// Settings types
export interface AppSettings {
  apiKey: string;
  apiUrl: string;
  model: 'gpt-3.5-turbo' | 'gpt-4' | 'gpt-4-turbo';
  temperature: number;
  maxTokens: number;
  chunkSize: number;
  chunkOverlap: number;
  topK: number;
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

export interface HealthResponse {
  status: 'healthy';
  version: string;
  timestamp: string;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

// Upload types
export interface UploadProgress {
  documentId: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
}

// Navigation types
export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  current?: boolean;
}
