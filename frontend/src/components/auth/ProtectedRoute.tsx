import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [] 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Simplified: Role check logic removed for now to align with current User model.
  // if (requiredRoles.length > 0 && user) {
  //   // Assuming user.is_superuser can map to an "admin" role for example.
  //   // This logic would need to be more robust if multiple roles are used.
  //   const userIsAdmin = user.is_superuser; // Example, assuming User model has is_superuser
  //   let hasRequiredRole = false;
  //   if (userIsAdmin && requiredRoles.includes('admin')) {
  //      hasRequiredRole = true;
  //   }
  //   // Add other role checks if necessary
  //   if (!hasRequiredRole && !requiredRoles.includes('user')) { // 'user' role might be default
  //     return <Navigate to="/unauthorized" replace />;
  //   }
  // }

  return <>{children}</>;
};

interface PublicRouteProps {
  children: React.ReactNode;
}

export const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
