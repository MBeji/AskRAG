import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthTokens, LoginCredentials, RegisterData } from '../types';
import { authService } from '../services/auth';

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [loading, setLoading] = useState(true);

  // Check for existing tokens on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedTokens = authService.getStoredTokens();
        if (storedTokens) {
          setTokens(storedTokens);
          // Verify token and get user info
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        authService.clearTokens();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      await authService.login(credentials); // authService.login now stores token internally
      const newTokens = authService.getStoredTokens();
      setTokens(newTokens);
      if (newTokens?.accessToken) {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } else {
        setUser(null); // Ensure user is cleared if token retrieval failed
      }
    } catch (error) {
      setUser(null); // Clear user/tokens on login failure
      setTokens(null);
      authService.clearTokens();
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setLoading(true);
      // authService.register now returns the created User, and does not log in.
      await authService.register(data);
      // After successful registration, user is not automatically logged in.
      // They need to go to the login page.
      // Consider showing a success message here.
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout(); // authService.logout already clears tokens from localStorage
    setUser(null);
    setTokens(null);
    // Optional: redirect to login or home page
    // window.location.href = '/login';
  };

  const refreshToken = async () => {
    try {
      if (!tokens?.refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const newTokens = await authService.refreshToken(tokens.refreshToken);
      setTokens(newTokens);
      authService.storeTokens(newTokens);
    } catch (error) {
      console.error('Failed to refresh token:', error);
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    tokens,
    loading,
    login,
    register,
    logout,
    refreshToken,
    isAuthenticated: !!user && !!tokens,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
