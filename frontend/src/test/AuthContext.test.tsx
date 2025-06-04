import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { ReactNode } from 'react';

// Mock the auth service
vi.mock('../services/auth', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn(),
  },
}));

// Test component to use the auth context
const TestComponent = () => {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth();
  
  return (
    <div>
      <div data-testid="auth-status">
        {isLoading ? 'loading' : isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user-email">{user?.email || 'no-user'}</div>
      <button data-testid="login-btn" onClick={() => login('test@example.com', 'password')}>
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

const renderWithAuthProvider = (children: ReactNode) => {
  return render(
    <AuthProvider>
      {children}
    </AuthProvider>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should provide initial auth state', () => {
    renderWithAuthProvider(<TestComponent />);
    
    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
  });

  it('should show loading state initially', () => {
    renderWithAuthProvider(<TestComponent />);
    
    // Should start with loading, then transition to not-authenticated
    expect(screen.getByTestId('auth-status')).toHaveTextContent('loading');
  });

  it('should handle successful login', async () => {
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

    const mockAuthService = await import('../services/auth');
    vi.mocked(mockAuthService.authService.login).mockResolvedValue({
      tokens: {
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        tokenType: 'bearer',
      },
      user: mockUser,
    });

    renderWithAuthProvider(<TestComponent />);
    
    const loginBtn = screen.getByTestId('login-btn');
    loginBtn.click();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    });
  });

  it('should handle logout', async () => {
    const mockAuthService = await import('../services/auth');
    vi.mocked(mockAuthService.authService.logout).mockResolvedValue();

    renderWithAuthProvider(<TestComponent />);
    
    const logoutBtn = screen.getByTestId('logout-btn');
    logoutBtn.click();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
    });
  });

  it('should restore authentication from localStorage', async () => {
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

    // Setup localStorage with existing tokens
    localStorage.setItem('accessToken', 'existing-token');
    localStorage.setItem('refreshToken', 'existing-refresh-token');

    const mockAuthService = await import('../services/auth');
    vi.mocked(mockAuthService.authService.getCurrentUser).mockResolvedValue(mockUser);

    renderWithAuthProvider(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    });
  });

  it('should handle authentication errors', async () => {
    const mockAuthService = await import('../services/auth');
    vi.mocked(mockAuthService.authService.login).mockRejectedValue(new Error('Invalid credentials'));

    renderWithAuthProvider(<TestComponent />);
    
    const loginBtn = screen.getByTestId('login-btn');
    loginBtn.click();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });
  });
});
