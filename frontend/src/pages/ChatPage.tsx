import React from 'react';
import NewChatInterface from '../components/NewChatInterface';
import ChatHistoryPanel from '../components/ChatHistoryPanel'; // Import the history panel
import { ChatProvider } from '../contexts/ChatContext'; // Import ChatProvider
import { useAuth } from '../contexts/AuthContext';

const ChatPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Chat with your Documents</h1>
        <p>Loading authentication status...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="p-6 text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Chat with your Documents</h1>
        <p className="text-gray-600">Please log in to access the chat functionality.</p>
      </div>
    );
  }

  // Basic inline styles for two-column layout
  const pageStyle: React.CSSProperties = {
    display: 'flex',
    height: 'calc(100vh - 64px)', // Example: Adjust based on actual header height in Layout.tsx
    // Assuming Layout.tsx header (h-16 -> 64px) is above this page.
    // If ChatPage is rendered inside Layout's <Outlet/>, this height should fill the Outlet area.
  };

  const historyPanelStyle: React.CSSProperties = {
    // width: '280px', // Defined in ChatHistoryPanel itself
    height: '100%',
    flexShrink: 0,
  };

  const chatInterfaceStyle: React.CSSProperties = {
    flexGrow: 1,
    height: '100%',
    display: 'flex',       // Added for NewChatInterface to flex correctly
    flexDirection: 'column' // Added for NewChatInterface to flex correctly
  };

  return (
    <ChatProvider> {/* Wrap with ChatProvider */}
      <div style={pageStyle}>
        <div style={historyPanelStyle}>
          <ChatHistoryPanel />
        </div>
        <div style={chatInterfaceStyle}>
          <NewChatInterface />
        </div>
      </div>
    </ChatProvider>
  );
};

export default ChatPage;
