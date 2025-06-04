import axios from 'axios';
import { User, /*AuthResponse,*/ AuthTokens, LoginCredentials, RegisterData, PasswordResetRequest, PasswordReset } from '../types';

// Define a simpler AuthResponse type to match current backend
interface BackendLoginResponse {
  access_token: string;
  token_type: string;
}
class AuthService {
  private readonly API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // Standardized to VITE_API_BASE_URL
  private readonly TOKEN_KEY = 'askrag_tokens'; // Stores AuthTokens { accessToken, refreshToken? }

  private api = axios.create({
    baseURL: `${this.API_BASE_URL}/api/v1`, // Correctly forms http://localhost:8000/api/v1
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  constructor() {
    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const tokens = this.getStoredTokens();
        if (tokens?.accessToken) {
          config.headers.Authorization = `Bearer ${tokens.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const tokens = this.getStoredTokens();
            if (tokens?.refreshToken) {
              const newTokens = await this.refreshToken(tokens.refreshToken);
              this.storeTokens(newTokens);
              originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<BackendLoginResponse> { // Return type matches current backend
    const formData = new FormData();
    // The backend's OAuth2PasswordRequestForm expects 'username', not 'email' for the username field.
    // If credentials.email is indeed the username, this is fine.
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await this.api.post<BackendLoginResponse>('/auth/login', formData, { // Path is relative to baseURL
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded', // Correct for OAuth2PasswordRequestForm
      },
    });

    // Backend returns {access_token, token_type}. Store it.
    // The existing storeTokens expects AuthTokens (accessToken, refreshToken).
    // Adapt by storing only the access token for now.
    if (response.data.access_token) {
      this.storeTokens({ accessToken: response.data.access_token, refreshToken: null }); // No refresh token from current backend
    }
    return response.data;
  }

  async register(data: RegisterData): Promise<User> { // Assuming register returns User (UserOut schema)
    const response = await this.api.post<User>('/auth/register', data); // Path is relative to baseURL
    // No token returned on register by current backend, so no token storage here.
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      this.clearTokens();
    }
  }

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await this.api.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/me');
    return response.data;
  }

  // Password reset methods
  async requestPasswordReset(data: PasswordResetRequest): Promise<{ message: string }> {
    const response = await this.api.post('/auth/password-reset-request', data);
    return response.data;
  }

  async resetPassword(data: PasswordReset): Promise<{ message: string }> {
    const response = await this.api.post('/auth/password-reset', data);
    return response.data;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await this.api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  }

  // Token management
  storeTokens(tokens: AuthTokens): void { // AuthTokens might need adjustment if refreshToken is not always present
    localStorage.setItem(this.TOKEN_KEY, JSON.stringify(tokens));
  }

  getStoredTokens(): AuthTokens | null { // This will now return { accessToken: string, refreshToken: null }
    const tokens = localStorage.getItem(this.TOKEN_KEY);
    return tokens ? JSON.parse(tokens) : null;
  }

  clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  // Utility methods
  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      return payload.exp < now;
    } catch (error) {
      return true;
    }
  }

  hasRole(user: User | null, roles: string[]): boolean {
    if (!user) return false;
    return roles.includes(user.role);
  }

  isAdmin(user: User | null): boolean {
    return this.hasRole(user, ['ADMIN', 'SUPERUSER']);
  }

  isSuperUser(user: User | null): boolean {
    return this.hasRole(user, ['SUPERUSER']);
  }
}

export const authService = new AuthService();
