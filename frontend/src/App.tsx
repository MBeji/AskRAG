import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout'; // Assuming Layout handles main nav and structure
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import React from 'react';
// Import ProtectedRoute and PublicRoute
import { ProtectedRoute, PublicRoute } from './components/auth/ProtectedRoute';

// Import actual pages
import HomePage from './pages/HomePage'; // Assuming HomePage.tsx exists or is a similar placeholder
import ChatPage from './pages/ChatPage';   // Assuming ChatPage.tsx exists
import DocumentsPage from './pages/DocumentsPage'; // Import actual DocumentsPage
import SettingsPage from './pages/SettingsPage'; // Assuming SettingsPage.tsx exists
import UserProfilePage from './pages/UserProfilePage'; // Assuming UserProfilePage.tsx exists

// If HomePage and others are just placeholders like this, they can stay.
// const HomePage = () => <div><h2>Home Page (Protected)</h2><p>Welcome!</p></div>;
// const ChatPage = () => <div><h2>Chat Page (Protected)</h2></div>;
// const SettingsPage = () => <div><h2>Settings Page (Protected)</h2></div>;
// const UserProfilePage = () => <div><h2>User Profile (Protected)</h2></div>;


function AppContent() {
  // This component can consume auth context if needed, e.g. for global error display
  // For now, it just sets up the routes.
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

      {/* Protected Routes within Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<UserProfilePage />} />
        {/* Add other protected routes here, they will render inside Layout's <Outlet /> */}
      </Route>

      {/* Fallback for unmatched routes or a 404 component */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;
