import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authService } from '../services/auth';
import axios from 'axios';

// Mock axios
vi.mock('axios');
const mockAxios = vi.mocked(axios, true);

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockResponse = {
        data: {
          tokens: {
            accessToken: 'access-token',
            refreshToken: 'refresh-token',
            tokenType: 'bearer',
          },
          user: {
            id: 'user-123',
            email: 'test@example.com',
            firstName: 'Test',
            lastName: 'User',
            role: 'USER',
            isActive: true,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        },
      };

      mockAxios.post.mockResolvedValue(mockResponse);

      const result = await authService.login('test@example.com', 'password123');

      expect(mockAxios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });

      expect(result).toEqual(mockResponse.data);
      expect(localStorage.getItem('accessToken')).toBe('access-token');
      expect(localStorage.getItem('refreshToken')).toBe('refresh-token');
    });

    it('should throw error for invalid credentials', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { error: 'Invalid credentials' },
        },
      };

      mockAxios.post.mockRejectedValue(mockError);

      await expect(authService.login('invalid@example.com', 'wrong')).rejects.toThrow();
    });
  });

  describe('register', () => {
    it('should register successfully with valid data', async () => {
      const mockResponse = {
        data: {
          tokens: {
            accessToken: 'access-token',
            refreshToken: 'refresh-token',
            tokenType: 'bearer',
          },
          user: {
            id: 'user-124',
            email: 'newuser@example.com',
            firstName: 'New',
            lastName: 'User',
            role: 'USER',
            isActive: true,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        },
      };

      mockAxios.post.mockResolvedValue(mockResponse);

      const userData = {
        email: 'newuser@example.com',
        password: 'password123',
        firstName: 'New',
        lastName: 'User',
      };

      const result = await authService.register(userData);

      expect(mockAxios.post).toHaveBeenCalledWith('/api/v1/auth/register', userData);
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error for existing user', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'User already exists' },
        },
      };

      mockAxios.post.mockRejectedValue(mockError);

      const userData = {
        email: 'existing@example.com',
        password: 'password123',
        firstName: 'Existing',
        lastName: 'User',
      };

      await expect(authService.register(userData)).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('should clear tokens from localStorage', async () => {
      localStorage.setItem('accessToken', 'token');
      localStorage.setItem('refreshToken', 'refresh');

      await authService.logout();

      expect(localStorage.getItem('accessToken')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user with valid token', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'USER',
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };

      mockAxios.get.mockResolvedValue({ data: mockUser });
      localStorage.setItem('accessToken', 'valid-token');

      const result = await authService.getCurrentUser();

      expect(mockAxios.get).toHaveBeenCalledWith('/api/v1/auth/me');
      expect(result).toEqual(mockUser);
    });

    it('should return null if no token', async () => {
      const result = await authService.getCurrentUser();
      expect(result).toBeNull();
    });

    it('should handle expired token', async () => {
      localStorage.setItem('accessToken', 'expired-token');
      
      const mockError = {
        response: {
          status: 401,
          data: { error: 'Token expired' },
        },
      };

      mockAxios.get.mockRejectedValue(mockError);

      await expect(authService.getCurrentUser()).rejects.toThrow();
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      const mockResponse = {
        data: {
          tokens: {
            accessToken: 'new-access-token',
            refreshToken: 'new-refresh-token',
            tokenType: 'bearer',
          },
        },
      };

      mockAxios.post.mockResolvedValue(mockResponse);
      localStorage.setItem('refreshToken', 'current-refresh-token');

      const result = await authService.refreshToken();

      expect(mockAxios.post).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        refreshToken: 'current-refresh-token',
      });

      expect(result).toEqual(mockResponse.data);
      expect(localStorage.getItem('accessToken')).toBe('new-access-token');
      expect(localStorage.getItem('refreshToken')).toBe('new-refresh-token');
    });

    it('should return null if no refresh token', async () => {
      const result = await authService.refreshToken();
      expect(result).toBeNull();
    });
  });

  describe('token management', () => {
    it('should get access token from localStorage', () => {
      localStorage.setItem('accessToken', 'test-token');
      expect(authService.getAccessToken()).toBe('test-token');
    });

    it('should return null if no access token', () => {
      expect(authService.getAccessToken()).toBeNull();
    });

    it('should check if user is authenticated', () => {
      expect(authService.isAuthenticated()).toBe(false);
      
      localStorage.setItem('accessToken', 'test-token');
      expect(authService.isAuthenticated()).toBe(true);
    });
  });
});
