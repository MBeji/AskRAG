import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { AuthProvider } from '../../contexts/AuthContext';
import { ToastProvider } from '../../contexts/ToastContext';
import UserProfile from '../../components/user/UserProfile';
import '@testing-library/jest-dom';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock auth context
const mockUser = {
  id: '1',
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  role: 'USER',
  isActive: true,
  createdAt: '2023-01-01T00:00:00Z'
};

const mockAuthContext = {
  user: mockUser,
  isAuthenticated: true,
  loading: false,
  login: vi.fn(),
  logout: vi.fn(),
  updateUser: vi.fn(),
};

vi.mock('../../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => mockAuthContext,
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

const renderWithProviders = (ui: React.ReactElement) => {
  return render(ui, { wrapper: AllTheProviders });
};

describe('UserProfile Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders user profile with user information', () => {
    renderWithProviders(<UserProfile />);
    
    expect(screen.getByText('User Profile')).toBeInTheDocument();
    expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('USER')).toBeInTheDocument();
  });

  it('updates profile information', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ 
        ...mockUser, 
        firstName: 'Jane',
        lastName: 'Smith' 
      }),
    });

    renderWithProviders(<UserProfile />);
    
    const firstNameInput = screen.getByDisplayValue('John');
    const lastNameInput = screen.getByDisplayValue('Doe');
    const saveButton = screen.getByRole('button', { name: /save profile/i });
    
    fireEvent.change(firstNameInput, { target: { value: 'Jane' } });
    fireEvent.change(lastNameInput, { target: { value: 'Smith' } });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/profile', expect.objectContaining({
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          firstName: 'Jane',
          lastName: 'Smith',
          email: 'test@example.com'
        })
      }));
    });
  });

  it('handles profile update error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Update failed'));

    renderWithProviders(<UserProfile />);
    
    const saveButton = screen.getByRole('button', { name: /save profile/i });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText('Update failed')).toBeInTheDocument();
    });
  });

  it('changes password successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: 'Password updated successfully' }),
    });

    renderWithProviders(<UserProfile />);
    
    const currentPasswordInput = screen.getByLabelText('Current Password');
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    
    fireEvent.change(currentPasswordInput, { target: { value: 'oldpassword' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.click(changePasswordButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/change-password', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPassword: 'oldpassword',
          newPassword: 'newpassword123'
        })
      }));
    });
  });

  it('validates password confirmation', () => {
    renderWithProviders(<UserProfile />);
    
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    
    fireEvent.change(newPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'differentpassword' } });
    fireEvent.click(changePasswordButton);
    
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('handles password change error with API response', async () => {
    const errorResponse = {
      ok: false,
      json: () => Promise.resolve({ detail: 'Current password is incorrect' }),
    };
    mockFetch.mockResolvedValueOnce(errorResponse);

    renderWithProviders(<UserProfile />);
    
    const currentPasswordInput = screen.getByLabelText('Current Password');
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    
    fireEvent.change(currentPasswordInput, { target: { value: 'wrongpassword' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.click(changePasswordButton);
    
    await waitFor(() => {
      expect(screen.getByText('Current password is incorrect')).toBeInTheDocument();
    });
  });

  it('clears password fields after successful change', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: 'Password updated successfully' }),
    });

    renderWithProviders(<UserProfile />);
    
    const currentPasswordInput = screen.getByLabelText('Current Password') as HTMLInputElement;
    const newPasswordInput = screen.getByLabelText('New Password') as HTMLInputElement;
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password') as HTMLInputElement;
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    
    fireEvent.change(currentPasswordInput, { target: { value: 'oldpassword' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.click(changePasswordButton);
    
    await waitFor(() => {
      expect(currentPasswordInput.value).toBe('');
      expect(newPasswordInput.value).toBe('');
      expect(confirmPasswordInput.value).toBe('');
    });
  });

  it('shows loading state during profile update', async () => {
    // Mock a slow response
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve(mockUser)
      }), 100))
    );

    renderWithProviders(<UserProfile />);
    
    const saveButton = screen.getByRole('button', { name: /save profile/i });
    fireEvent.click(saveButton);
    
    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

  it('shows loading state during password change', async () => {
    // Mock a slow response
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Success' })
      }), 100))
    );

    renderWithProviders(<UserProfile />);
    
    const currentPasswordInput = screen.getByLabelText('Current Password');
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    
    fireEvent.change(currentPasswordInput, { target: { value: 'oldpassword' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.click(changePasswordButton);
    
    expect(screen.getByText('Changing...')).toBeInTheDocument();
  });
});
