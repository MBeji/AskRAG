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

// Chat types (Updated for Step 21 to match backend schemas)

// This SearchResultItem should match what's returned by the backend's /rag/search
// and used in QueryResponse sources. It's also used by ChatMessage sources.
export interface SearchResultItem {
  document_id: string;
  chunk_index: number;
  chunk_text: string;
  source_filename: string;
  score?: number;
  upload_date?: string; // ISO string date
}

export interface ChatMessage { // Corresponds to backend ChatMessageResponse
  message_id: string;
  sender: 'user' | 'bot'; // Was 'type' before, standardizing to 'sender'
  text: string;           // Was 'content' before, standardizing to 'text'
  timestamp: string;      // ISO string date
  sources?: SearchResultItem[];
}

export interface ChatSession { // Corresponds to backend ChatSessionResponse
  id: string;
  user_id: string;
  title?: string | null;
  created_at: string;     // ISO string date
  updated_at: string;     // ISO string date
  messages: ChatMessage[];
}

export interface ChatSessionListItem { // Corresponds to backend ChatSessionListItem
  id: string;
  user_id: string;
  title?: string | null;
  created_at: string;     // ISO string date
  updated_at: string;     // ISO string date
  last_message_snippet?: string | null;
}

// RAG Query Response from Step 18, now including session_id
export interface RAGQueryResponse {
  answer: string;
  sources: SearchResultItem[];
  session_id: string; // session_id is PydanticObjectId on backend, string here
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
