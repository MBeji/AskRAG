import React, { useEffect } from 'react';
import { useChat } from '../contexts/ChatContext';
import { ChatSessionListItem } from '../types'; // Assuming types are in ../types
import { PlusCircleIcon, ChatBubbleLeftEllipsisIcon } from '@heroicons/react/24/outline';

const ChatHistoryPanel: React.FC = () => {
  const {
    sessions,
    currentSessionId,
    isLoadingSessions,
    fetchSessions,
    loadSession,
    startNewChat
  } = useChat();

  useEffect(() => {
    // Fetch sessions when the component mounts, if not already loaded by ChatContext
    // ChatContext already fetches on auth change, so this might be redundant
    // but can be kept for explicit refresh or initial load if context didn't run yet.
    if (sessions.length === 0) {
      fetchSessions();
    }
  }, [fetchSessions, sessions.length]);

  const handleSessionClick = (sessionId: string) => {
    if (sessionId !== currentSessionId) {
      loadSession(sessionId);
    }
  };

  const handleNewChat = () => {
    startNewChat();
  };

  // Basic inline styles - can be replaced with Tailwind or CSS Modules
  const styles = {
    panel: {
      width: '280px',
      borderRight: '1px solid #e0e0e0',
      padding: '10px',
      backgroundColor: '#f9f9f9',
      display: 'flex',
      flexDirection: 'column',
      height: '100%', // Ensure it takes full height of its container
    } as React.CSSProperties,
    header: {
      paddingBottom: '10px',
      marginBottom: '10px',
      borderBottom: '1px solid #e0e0e0',
    } as React.CSSProperties,
    title: {
      fontSize: '1.1em',
      fontWeight: 'bold',
      color: '#333',
    } as React.CSSProperties,
    newChatButton: {
      display: 'flex',
      alignItems: 'center',
      width: '100%',
      padding: '10px',
      marginBottom: '10px',
      borderRadius: '5px',
      border: '1px dashed #007bff',
      color: '#007bff',
      backgroundColor: 'white',
      cursor: 'pointer',
      textAlign: 'left',
    } as React.CSSProperties,
    sessionList: {
      flexGrow: 1,
      overflowY: 'auto',
      listStyle: 'none',
      padding: 0,
      margin: 0,
    } as React.CSSProperties,
    sessionItem: (isActive: boolean) => ({
      padding: '10px',
      marginBottom: '5px',
      borderRadius: '5px',
      cursor: 'pointer',
      backgroundColor: isActive ? '#007bff' : 'transparent',
      color: isActive ? 'white' : '#333',
      border: isActive ? 'none' : '1px solid transparent',
    } as React.CSSProperties),
    sessionTitle: {
      fontWeight: '500',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
    } as React.CSSProperties,
    sessionDate: {
      fontSize: '0.8em',
      opacity: 0.7,
    } as React.CSSProperties,
  };

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <h2 style={styles.title}>Chat History</h2>
      </div>
      <button onClick={handleNewChat} style={styles.newChatButton}>
        <PlusCircleIcon style={{ width: '20px', height: '20px', marginRight: '8px' }} />
        New Chat
      </button>
      {isLoadingSessions && <p>Loading sessions...</p>}
      {!isLoadingSessions && sessions.length === 0 && (
        <p style={{ textAlign: 'center', color: '#777', marginTop: '20px' }}>No chat sessions yet.</p>
      )}
      <ul style={styles.sessionList}>
        {sessions.map((session: ChatSessionListItem) => (
          <li
            key={session.id}
            style={styles.sessionItem(session.id === currentSessionId)}
            onClick={() => handleSessionClick(session.id)}
            title={session.title || `Chat from ${new Date(session.created_at).toLocaleDateString()}`}
          >
            <div style={styles.sessionTitle}>
              <ChatBubbleLeftEllipsisIcon style={{ width: '16px', height: '16px', marginRight: '5px', display: 'inline-block', verticalAlign: 'middle' }} />
              {session.title || `Chat - ${session.id.substring(0, 8)}`}
            </div>
            <div style={styles.sessionDate}>
              {new Date(session.updated_at).toLocaleString()}
            </div>
            {session.last_message_snippet && (
              <p style={{ fontSize: '0.8em', opacity: 0.8, fontStyle: 'italic', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: '4px'}}>
                {session.last_message_snippet}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ChatHistoryPanel;
