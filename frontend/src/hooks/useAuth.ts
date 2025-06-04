import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/auth';
import { User, LoginCredentials, RegisterData, PasswordResetRequest, PasswordReset } from '../types';

// Login hook
export const useLogin = () => {
  const { login } = useAuth();
  
  return useMutation({
    mutationFn: (credentials: LoginCredentials) => login(credentials),
    onError: (error) => {
      console.error('Login failed:', error);
    },
  });
};

// Register hook
export const useRegister = () => {
  const { register } = useAuth();
  
  return useMutation({
    mutationFn: (data: RegisterData) => register(data),
    onError: (error) => {
      console.error('Registration failed:', error);
    },
  });
};

// Logout hook
export const useLogout = () => {
  const { logout } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      await authService.logout();
      logout();
    },
    onSuccess: () => {
      queryClient.clear();
    },
  });
};

// Password reset request hook
export const usePasswordResetRequest = () => {
  return useMutation({
    mutationFn: (data: PasswordResetRequest) => authService.requestPasswordReset(data),
  });
};

// Password reset hook
export const usePasswordReset = () => {
  return useMutation({
    mutationFn: (data: PasswordReset) => authService.resetPassword(data),
  });
};

// Change password hook
export const useChangePassword = () => {
  return useMutation({
    mutationFn: ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) =>
      authService.changePassword(currentPassword, newPassword),
  });
};

// Get current user hook
export const useCurrentUser = () => {
  const { user, isAuthenticated } = useAuth();
  
  return useQuery({
    queryKey: ['auth', 'currentUser'],
    queryFn: () => authService.getCurrentUser(),
    enabled: isAuthenticated,
    initialData: user,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Refresh token hook
export const useRefreshToken = () => {
  const { refreshToken } = useAuth();
  
  return useMutation({
    mutationFn: () => refreshToken(),
  });
};
