import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { AuthProvider } from '../../contexts/AuthContext';
import { ToastProvider } from '../../contexts/ToastContext';
import LoginPage from '../../pages/auth/LoginPage';

// Mock the auth service
vi.mock('../../services/auth', () => ({
  authService: {
    login: vi.fn(),
    getStoredTokens: vi.fn(() => null),
    getCurrentUser: vi.fn(),
    clearTokens: vi.fn(), // Added missing method
    storeTokens: vi.fn(), // Added missing method
  },
}));

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            {children}
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

const renderWithProviders = (component: React.ReactElement) => {
  return render(component, { wrapper: AllTheProviders });
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form elements', () => {
    renderWithProviders(<LoginPage />);
    
    expect(screen.getByRole('heading', { name: /sign in to askrag/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows password visibility toggle', () => {
    renderWithProviders(<LoginPage />);
    
    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i });
    
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('validates required fields', async () => {
    renderWithProviders(<LoginPage />);
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);
    
    // HTML5 validation should prevent submission
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    expect(emailInput).toBeRequired();
    expect(passwordInput).toBeRequired();
  });

  it('shows loading state during login', async () => {
    const { authService } = await import('../../services/auth');
    (authService.login as any).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderWithProviders(<LoginPage />);
    
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument();
  });

  it('displays error message on login failure', async () => {
    const { authService } = await import('../../services/auth');
    (authService.login as any).mockRejectedValue(new Error('Invalid credentials'));
    
    renderWithProviders(<LoginPage />);
    
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrongpassword' },
    });
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('redirects to register page', () => {
    renderWithProviders(<LoginPage />);
    
    const registerLink = screen.getByRole('link', { name: /sign up/i });
    expect(registerLink).toHaveAttribute('href', '/register');
  });

  it('redirects to forgot password page', () => {
    renderWithProviders(<LoginPage />);
    
    const forgotPasswordLink = screen.getByRole('link', { name: /forgot your password/i });
    expect(forgotPasswordLink).toHaveAttribute('href', '/forgot-password');
  });
});
