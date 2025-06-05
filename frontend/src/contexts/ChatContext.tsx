import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { ChatSession, ChatSessionListItem, ChatMessage, RAGQueryResponse } from '../types'; // Assuming types are in ../types
import { getChatSessions, getChatSession, askRAG } from '../services/api';
import { useAuth } from './AuthContext'; // To ensure user is authenticated

interface ChatContextType {
  sessions: ChatSessionListItem[];
  currentSession: ChatSession | null;
  currentSessionId: string | null;
  isLoadingSessions: boolean;
  isLoadingMessages: boolean; // For loading messages of a specific session or waiting for bot
  fetchSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  startNewChat: () => void; // Clears current session, new one created on first message
  sendMessage: (query: string) => Promise<void>; // Will handle user message and bot response
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState<ChatSessionListItem[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false); // Used for RAG response

  const fetchSessions = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsLoadingSessions(true);
    try {
      const fetchedSessions = await getChatSessions();
      setSessions(fetchedSessions);
    } catch (error) {
      console.error("Failed to fetch chat sessions:", error);
      // Optionally set an error state here
    } finally {
      setIsLoadingSessions(false);
    }
  }, [isAuthenticated]);

  // Fetch sessions when user becomes authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchSessions();
    } else {
      // Clear sessions if user logs out
      setSessions([]);
      setCurrentSession(null);
      setCurrentSessionId(null);
    }
  }, [isAuthenticated, fetchSessions]);

  const loadSession = useCallback(async (sessionId: string) => {
    if (!isAuthenticated) return;
    setIsLoadingMessages(true); // Use this for loading the selected session's messages
    setCurrentSessionId(sessionId);
    try {
      const sessionDetails = await getChatSession(sessionId);
      setCurrentSession(sessionDetails);
    } catch (error) {
      console.error(`Failed to load session ${sessionId}:`, error);
      setCurrentSession(null); // Clear if error
      // Optionally set an error state
    } finally {
      setIsLoadingMessages(false);
    }
  }, [isAuthenticated]);

  const startNewChat = useCallback(() => {
    setCurrentSession(null);
    setCurrentSessionId(null); // New session ID will be set by backend on first message
  }, []);

  const addMessageToCurrentSessionOptimistically = (message: ChatMessage) => {
    if (currentSession) {
      setCurrentSession(prev => prev ? { ...prev, messages: [...prev.messages, message] } : null);
    } else {
      // This is a new chat, create a temporary session structure for immediate display
      // The actual session ID will come from the backend.
      setCurrentSession({
        id: 'temp-new-session', // Temporary ID
        user_id: '', // Will be set by backend
        title: message.text.substring(0, 30) + "...",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: [message],
      });
    }
  };

  const sendMessage = async (query: string) => {
    if (!isAuthenticated) {
      throw new Error("User is not authenticated.");
    }
    setIsLoadingMessages(true);

    const userMessage: ChatMessage = {
      message_id: `user-${Date.now()}`,
      text: query,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };

    // Optimistic update for user message
    addMessageToCurrentSessionOptimistically(userMessage);

    try {
      const response: RAGQueryResponse = await askRAG(query, currentSessionId);

      const botMessage: ChatMessage = {
        message_id: `bot-${Date.now()}`, // Backend might provide actual ID later if needed
        text: response.answer,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        sources: response.sources,
      };

      // Update session based on response
      if (currentSessionId === null || currentSessionId === 'temp-new-session' || currentSessionId !== response.session_id) {
        // This was a new chat, or backend assigned a new session ID. Fetch the full session.
        setCurrentSessionId(response.session_id);
        await loadSession(response.session_id); // This will load all messages including the new ones
      } else {
        // Existing session, just add the bot message optimistically
        // For robustness, it's better to refetch the session or ensure messages are consistent
        // For now, just add to current session, assuming backend saved it.
         setCurrentSession(prev => {
           if (prev && prev.id === response.session_id) {
             return { ...prev, messages: [...prev.messages, botMessage], updated_at: new Date().toISOString() };
           }
           return prev; // Should not happen if session ID matches
         });
      }
      // Refresh session list to reflect updated_at changes
      await fetchSessions();

    } catch (error) {
      console.error("Failed to send message or get RAG response:", error);
      // Optionally add an error message to chat
      const errorMessage: ChatMessage = {
        message_id: `error-${Date.now()}`,
        text: "Error sending message. Please try again.",
        sender: 'bot',
        timestamp: new Date().toISOString(),
      };
      addMessageToCurrentSessionOptimistically(errorMessage); // Add error to current display
      throw error; // Rethrow for component to handle if needed
    } finally {
      setIsLoadingMessages(false);
    }
  };


  return (
    <ChatContext.Provider value={{
      sessions,
      currentSession,
      currentSessionId,
      isLoadingSessions,
      isLoadingMessages,
      fetchSessions,
      loadSession,
      startNewChat,
      sendMessage
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
