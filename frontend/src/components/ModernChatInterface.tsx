import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { 
  PaperAirplaneIcon, 
  DocumentArrowUpIcon, 
  LinkIcon,
  XMarkIcon,
  EyeIcon,
  GlobeAltIcon,
  SparklesIcon,
  UserIcon,
  CpuChipIcon,
  ArrowRightOnRectangleIcon,
  FolderIcon,
  MagnifyingGlassIcon,
  CogIcon,
  CommandLineIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import { useSimpleAuth } from '../hooks/useSimpleAuth';
import { useNotifications } from '../hooks/useNotifications';
import LoginModal from './LoginModal';
import DocumentManager from './DocumentManager';
import NotificationContainer from './NotificationContainer';
import SettingsModal from './SettingsModal';
import ChatSearch from './ChatSearch';
import QuickActionsPanel from './QuickActionsPanel';
import ErrorBoundary from './ErrorBoundary';
import ScrollIndicator from './ScrollIndicator';
import KeyboardShortcutsModal from './KeyboardShortcutsModal';
import PerformanceMonitor from './PerformanceMonitor';
import '../styles/modern-dark-theme.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  files?: File[];
  urls?: string[];
}

interface FilePreview {
  file: File;
  id: string;
}

interface URLPreview {
  url: string;
  id: string;
  title?: string;
  favicon?: string;
}

// Utility function to generate session ID
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const ModernChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<FilePreview[]>([]);
  const [urlInputValue, setUrlInputValue] = useState('');
  const [urlPreviews, setUrlPreviews] = useState<URLPreview[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showDocumentManager, setShowDocumentManager] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);  const [showChatSearch, setShowChatSearch] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false);
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const { user, isAuthenticated, login, logout, getAuthHeaders, isLoading: authLoading, error: authError } = useSimpleAuth();
  const { notifications, removeNotification, success, error: notifyError, warning, info } = useNotifications();

  // Performance optimization: Memoize expensive operations
  const memoizedMessages = useMemo(() => {
    // Only show last 50 messages for performance, can be made configurable
    const MAX_VISIBLE_MESSAGES = 50;
    return messages.length > MAX_VISIBLE_MESSAGES 
      ? messages.slice(-MAX_VISIBLE_MESSAGES) 
      : messages;
  }, [messages]);

  // Memoized file operations
  const fileOperations = useMemo(() => ({
    addFiles: useCallback((files: File[]) => {
      const newFiles = files.map(file => ({
        file,
        id: `file-${Date.now()}-${Math.random()}`
      }));
      setUploadedFiles(prev => [...prev, ...newFiles]);
      
      if (files.length === 1) {
        info('File Added', `${files[0].name} is ready for upload`);
      } else {
        info('Files Added', `${files.length} files are ready for upload`);
      }
    }, [info]),
    
    removeFile: useCallback((id: string) => {
      setUploadedFiles(prev => prev.filter(f => f.id !== id));
    }, [])
  }), [info]);

  // Memoized URL operations
  const urlOperations = useMemo(() => ({
    addUrl: useCallback(() => {
      if (urlInputValue.trim()) {
        const newUrl: URLPreview = {
          url: urlInputValue.trim(),
          id: `url-${Date.now()}-${Math.random()}`,
          title: extractDomainFromUrl(urlInputValue.trim()),
          favicon: `https://www.google.com/s2/favicons?domain=${extractDomainFromUrl(urlInputValue.trim())}&sz=32`
        };
        setUrlPreviews(prev => [...prev, newUrl]);
        setUrlInputValue('');
        success('Link Added', `${newUrl.title} has been added to your context`);
      }
    }, [urlInputValue, success]),
    
    removeUrl: useCallback((id: string) => {
      setUrlPreviews(prev => prev.filter(u => u.id !== id));
    }, [])
  }), [urlInputValue, success]);

  // Performance monitoring for large conversations
  useEffect(() => {
    if (messages.length > 100) {
      console.log(`Performance note: Large conversation with ${messages.length} messages. Consider using virtualization for better performance.`);
    }
  }, [messages.length]);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8003';
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);  // Initialize session when authenticated
  useEffect(() => {
    if (isAuthenticated && !sessionId) {
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
      info('Session Started', 'New conversation session created');
      // Load chat history for the new session
      loadChatHistory(newSessionId);
    } else if (!isAuthenticated) {
      setSessionId(null);
      setMessages([]); // Clear messages when logged out
    }
  }, [isAuthenticated, sessionId]);
  // Load chat history for a session
  const loadChatHistory = async (currentSessionId: string) => {
    if (!isAuthenticated) return;
    
    try {
      const authHeaders = getAuthHeaders();
      const response = await fetch(`${API_BASE}/api/v1/chat/history/${currentSessionId}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(authHeaders.Authorization ? { Authorization: authHeaders.Authorization } : {}),
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.messages && Array.isArray(data.messages)) {
          const formattedMessages: Message[] = data.messages.map((msg: any) => ({
            id: msg.id || `msg-${Date.now()}-${Math.random()}`,
            type: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content,
            timestamp: new Date(msg.timestamp),
          }));
          setMessages(formattedMessages);
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  // Save chat messages to backend
  const saveChatMessage = async (userMessage: Message, assistantMessage: Message, currentSessionId: string) => {
    if (!isAuthenticated) return;
    
    try {
      const authHeaders = getAuthHeaders();
      await fetch(`${API_BASE}/api/v1/chat/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authHeaders.Authorization ? { Authorization: authHeaders.Authorization } : {}),
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          messages: [
            {
              role: 'user',
              content: userMessage.content,
              timestamp: userMessage.timestamp.toISOString(),
            },
            {
              role: 'assistant',
              content: assistantMessage.content,
              timestamp: assistantMessage.timestamp.toISOString(),
            }
          ]
        }),
      });
    } catch (error) {
      console.error('Failed to save chat message:', error);
    }
  };

  // Handle drag and drop
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    if (!chatContainerRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    fileOperations.addFiles(files);
  };  const addFiles = fileOperations.addFiles;
  const removeFile = fileOperations.removeFile;
  const addUrl = urlOperations.addUrl;
  const removeUrl = urlOperations.removeUrl;

  const extractDomainFromUrl = (url: string): string => {
    try {
      const domain = new URL(url.startsWith('http') ? url : `https://${url}`).hostname;
      return domain.replace('www.', '');
    } catch {
      return url;
    }
  };  const handleFileUpload = async (files: File[]): Promise<string[]> => {
    const uploadResults: string[] = [];
    
    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const authHeaders = getAuthHeaders();
        const headers: Record<string, string> = {};
        
        if (authHeaders.Authorization) {
          headers.Authorization = authHeaders.Authorization;
        }
        
        const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
          method: 'POST',
          body: formData,
          headers,
        });
        
        if (response.ok) {
          uploadResults.push(`✅ ${file.name} uploaded successfully`);
          success('File Uploaded', `${file.name} has been processed successfully`);
        } else if (response.status === 401) {
          uploadResults.push(`🔒 Please login to upload ${file.name}`);
          warning('Authentication Required', 'Please sign in to upload documents');
          setShowLoginModal(true);
        } else {
          uploadResults.push(`❌ Failed to upload ${file.name}`);
          notifyError('Upload Failed', `Could not upload ${file.name}. Please try again.`);
        }
      } catch (error) {
        console.error('Upload error:', error);
        uploadResults.push(`❌ Error uploading ${file.name}`);
        notifyError('Upload Error', `Network error while uploading ${file.name}`);
      }
    }
    
    return uploadResults;
  };
  const handleSendMessage = async () => {
    if (!inputValue.trim() && uploadedFiles.length === 0 && urlPreviews.length === 0) {
      return;
    }

    const newMessage: Message = {
      id: `msg-${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
      files: uploadedFiles.map(f => f.file),
      urls: urlPreviews.map(u => u.url)
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Upload files if any
      let uploadResults: string[] = [];
      if (uploadedFiles.length > 0) {
        uploadResults = await handleFileUpload(uploadedFiles.map(f => f.file));
      }

      // Process URLs if any
      const urlResults = urlPreviews.map(u => `🔗 URL added to context: ${u.url}`);

      // Send message to RAG system if authenticated
      let ragResponse = '';
      if (isAuthenticated && inputValue.trim()) {
        try {
          const authHeaders = getAuthHeaders();
          const ragRequest = {
            question: inputValue,
            session_id: sessionId || generateSessionId(),
            max_chunks: 5,
            include_sources: true
          };          const response = await fetch(`${API_BASE}/api/v1/rag/ask`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(authHeaders.Authorization ? { Authorization: authHeaders.Authorization } : {}),
            },
            body: JSON.stringify(ragRequest),
          });          if (response.ok) {
            const data = await response.json();
            ragResponse = data.answer || 'No response generated.';
            
            // Add sources if available
            if (data.sources && data.sources.length > 0) {
              ragResponse += '\n\n📚 **Sources:**\n' + data.sources.map((source: any, idx: number) => 
                `${idx + 1}. ${source.document_title || source.filename || 'Document'} ${source.page_number ? `(page ${source.page_number})` : ''}`
              ).join('\n');
              info('Sources Found', `Found ${data.sources.length} relevant source(s) for your question`);
            }
          } else if (response.status === 401) {
            ragResponse = '🔒 Please log in to access the AI assistant with your documents.';
            warning('Authentication Required', 'Please sign in to access full AI capabilities');
            setShowLoginModal(true);
          } else {
            ragResponse = '❌ Sorry, I encountered an error processing your question. Please try again.';
            notifyError('Processing Error', 'Failed to process your question. Please try again.');
          }        } catch (error) {
          console.error('RAG API error:', error);
          ragResponse = '🔗 Connection error. Using basic response mode.';
          warning('Connection Issue', 'Using offline mode. Please check your connection.');
        }
      } else if (!isAuthenticated && inputValue.trim()) {
        ragResponse = '🤖 I can help you with general questions, but to analyze your documents and provide detailed answers, please sign in to unlock the full AI assistant capabilities.';
      }

      // Combine all results
      const responseContent = [
        ragResponse,
        ...uploadResults,
        ...urlResults
      ].filter(Boolean).join('\n\n');

      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        type: 'assistant',
        content: responseContent || '🤖 Hello! How can I help you today?',
        timestamp: new Date()
      };      setMessages(prev => [...prev, assistantMessage]);
      
      // Save the conversation to backend if authenticated
      if (isAuthenticated && sessionId) {
        await saveChatMessage(newMessage, assistantMessage, sessionId);
      }
      
      // Store session ID for conversation continuity
      if (!sessionId && isAuthenticated) {
        setSessionId(generateSessionId());
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        type: 'assistant',
        content: '❌ Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setUploadedFiles([]);
      setUrlPreviews([]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  // Keyboard shortcuts and navigation
  useEffect(() => {
    const handleKeyboardShortcuts = (event: KeyboardEvent) => {
      // Only trigger if not typing in an input field
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (event.ctrlKey || event.metaKey) {
        switch (event.key.toLowerCase()) {
          case ' ':
            event.preventDefault();
            setShowQuickActions(true);
            break;
          case 'f':
            event.preventDefault();
            if (messages.length > 0) {
              setShowChatSearch(true);
            }
            break;
          case 'u':
            event.preventDefault();
            fileInputRef.current?.click();
            break;          case 'l':
            event.preventDefault();
            (document.querySelector('input[placeholder*="paste"]') as HTMLInputElement)?.focus();
            break;
          case 'n':
            event.preventDefault();
            handleNewChat();            break;
          case 'e':
            event.preventDefault();
            handleExportChat();
            break;
          case ',':
            event.preventDefault();
            setShowSettingsModal(true);
            break;          case 'd':
            event.preventDefault();
            if (isAuthenticated) {
              setShowDocumentManager(true);
            }
            break;
          case 'p':
            event.preventDefault();
            setShowPerformanceMonitor(!showPerformanceMonitor);
            break;
        }
      }

      // Arrow key navigation for messages
      if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        const messageElements = Array.from(document.querySelectorAll('[data-message-id]'));
        const currentFocus = document.activeElement;
        const currentIndex = messageElements.indexOf(currentFocus as Element);
        
        if (event.key === 'ArrowUp' && currentIndex > 0) {
          event.preventDefault();
          (messageElements[currentIndex - 1] as HTMLElement)?.focus();
        } else if (event.key === 'ArrowDown' && currentIndex < messageElements.length - 1) {
          event.preventDefault();
          (messageElements[currentIndex + 1] as HTMLElement)?.focus();
        } else if (event.key === 'ArrowDown' && currentIndex === -1 && messageElements.length > 0) {
          event.preventDefault();
          (messageElements[0] as HTMLElement)?.focus();
        }
      }      // ESC to close modals and clear focus
      if (event.key === 'Escape') {
        setShowQuickActions(false);
        setShowChatSearch(false);
        setShowSettingsModal(false);
        setShowUserMenu(false);
        setShowKeyboardShortcuts(false);
        setShowPerformanceMonitor(false);
        // Clear focus from messages when pressing escape
        if (document.activeElement?.hasAttribute('data-message-id')) {
          (document.activeElement as HTMLElement).blur();
        }
      }

      // ? to show keyboard shortcuts help
      if (event.key === '?' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        setShowKeyboardShortcuts(true);
      }

      // Enter to focus on input when a message is focused
      if (event.key === 'Enter' && document.activeElement?.hasAttribute('data-message-id')) {
        event.preventDefault();
        const inputElement = document.querySelector('textarea[placeholder*="Type"]') as HTMLTextAreaElement;
        inputElement?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyboardShortcuts);
    return () => document.removeEventListener('keydown', handleKeyboardShortcuts);
  }, [messages.length, isAuthenticated]);

  // Helper functions for new features
  const handleNewChat = () => {
    if (messages.length > 0) {
      const confirmed = window.confirm('Are you sure you want to start a new conversation? Current messages will be cleared.');
      if (!confirmed) return;
    }
    
    setMessages([]);
    setUploadedFiles([]);
    setUrlPreviews([]);
    setInputValue('');
    
    if (isAuthenticated) {
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
      info('New Chat Started', 'Fresh conversation session created');
    }
  };

  const handleExportChat = () => {
    if (messages.length === 0) {
      warning('No Messages', 'There are no messages to export');
      return;
    }

    const chatData = {
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      messages: messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
        files: msg.files?.map(f => f.name) || [],
        urls: msg.urls || []
      }))
    };

    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `askrag-chat-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    success('Chat Exported', 'Your conversation has been downloaded');
  };

  const handleClearChat = () => {
    const confirmed = window.confirm('Are you sure you want to clear all messages? This action cannot be undone.');
    if (confirmed) {
      setMessages([]);
      setUploadedFiles([]);
      setUrlPreviews([]);
      setInputValue('');
      info('Chat Cleared', 'All messages have been removed');
    }
  };

  const handleMessageSelect = (messageId: string) => {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      messageElement.classList.add('highlight-message');
      setTimeout(() => messageElement.classList.remove('highlight-message'), 2000);
    }
  };

  return (
    <div 
      className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/10 to-slate-900 relative"
      ref={chatContainerRef}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >      {/* Header */}
      <div className="glass-effect border-b border-white/10 p-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gradient mb-2">
              AskRAG
            </h1>
            <p className="text-slate-400 text-sm">
              Your intelligent document assistant with mystical powers
            </p>
          </div>          {/* User Menu */}
          <div className="flex items-center gap-4">
            {/* Quick Actions Button */}
            <button
              onClick={() => setShowQuickActions(true)}
              className="btn-secondary px-3 py-2 text-sm flex items-center gap-2"
              title="Quick Actions (Ctrl+Space)"
            >
              <CommandLineIcon className="w-4 h-4" />
              Actions
            </button>

            {/* Search Button */}
            {messages.length > 0 && (
              <button
                onClick={() => setShowChatSearch(true)}
                className="btn-secondary px-3 py-2 text-sm flex items-center gap-2"
                title="Search History (Ctrl+F)"
              >
                <MagnifyingGlassIcon className="w-4 h-4" />
                Search
              </button>
            )}            {/* Settings Button */}
            <button
              onClick={() => setShowSettingsModal(true)}
              className="btn-secondary px-3 py-2 text-sm flex items-center gap-2"
              title="Settings"
            >
              <CogIcon className="w-4 h-4" />
            </button>

            {/* Help Button */}
            <button
              onClick={() => setShowKeyboardShortcuts(true)}
              className="btn-secondary px-3 py-2 text-sm flex items-center gap-2"
              title="Keyboard Shortcuts (?)"
            >
              <QuestionMarkCircleIcon className="w-4 h-4" />
            </button>

            {/* Document Manager Button - Show when authenticated */}
            {isAuthenticated && (
              <button
                onClick={() => setShowDocumentManager(true)}
                className="btn-secondary px-4 py-2 text-sm flex items-center gap-2"
                title="Manage Documents"
              >
                <FolderIcon className="w-4 h-4" />
                Documents
              </button>
            )}
            
            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50 border border-slate-700 hover:bg-slate-700/50 transition-all"
                >
                  <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-teal-500 rounded-full flex items-center justify-center">
                    <UserIcon className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-slate-200">
                      {user.firstName} {user.lastName}
                    </p>
                    <p className="text-xs text-slate-400 capitalize">
                      {user.role}
                    </p>
                  </div>
                </button>
                
                {showUserMenu && (
                  <div className="absolute top-full right-0 mt-2 w-48 bg-slate-800/95 backdrop-blur-xl border border-slate-700 rounded-lg shadow-xl z-50">
                    <div className="p-2">
                      <button
                        onClick={() => {
                          logout();
                          setShowUserMenu(false);
                        }}
                        className="w-full flex items-center gap-2 p-2 text-left text-slate-300 hover:bg-slate-700/50 rounded-lg transition-colors"
                      >
                        <ArrowRightOnRectangleIcon className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setShowLoginModal(true)}
                className="btn-secondary px-4 py-2 text-sm"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>      {/* Main Chat Area */}
      <div className="max-w-4xl mx-auto p-6 flex flex-col h-[calc(100vh-120px)]">
        {/* Scroll Progress Indicator */}
        {messages.length > 3 && (
          <ScrollIndicator target={messagesContainerRef.current} />
        )}
          {/* Messages Container */}
        <div 
          ref={messagesContainerRef} 
          className="flex-1 overflow-y-auto space-y-4 mb-6" 
          id="messages-container"
          role="log"
          aria-live="polite"
          aria-label="Chat conversation"
        >
          {messages.length === 0 && (
            <div className="text-center py-12 fade-in">
              <div className="text-6xl mb-4">✨</div>
              <h2 className="text-2xl font-semibold text-slate-300 mb-2">
                Welcome to AskRAG
              </h2>
              <p className="text-slate-500 max-w-md mx-auto">
                Upload documents, share links, and chat with your intelligent assistant. 
                Let the magic begin...
              </p>
            </div>
          )}          {memoizedMessages.map((message, index) => (            <div
              key={message.id}
              data-message-id={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} slide-up`}
              role="article"
              aria-label={`${message.type === 'user' ? 'Your message' : 'Assistant response'} at ${message.timestamp.toLocaleTimeString()}`}
              tabIndex={0}
            >
              <div className={`flex items-start gap-3 max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                <div 
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' 
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500' 
                      : 'bg-gradient-to-r from-teal-500 to-emerald-500'
                  }`}
                  aria-label={message.type === 'user' ? 'User avatar' : 'Assistant avatar'}
                >
                  {message.type === 'user' ? (
                    <UserIcon className="w-5 h-5 text-white" />
                  ) : (
                    <CpuChipIcon className="w-5 h-5 text-white" />
                  )}
                </div>
                
                {/* Message Bubble */}
                <div 
                  className={`chat-bubble ${message.type} relative group`}
                  role="region"
                  aria-label={`Message content from ${message.type}`}
                >
                  <div 
                    className="whitespace-pre-wrap"
                    aria-label="Message text"
                  >
                    {message.content}
                  </div>
                  <div 
                    className="text-xs opacity-70 mt-2 flex items-center justify-between"
                    aria-label={`Message sent at ${message.timestamp.toLocaleString()}`}
                  >
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.type === 'assistant' && (
                      <SparklesIcon className="w-3 h-3 opacity-50" aria-label="AI generated response" />
                    )}
                  </div>
                  
                  {/* Message actions */}
                  <div className="absolute -top-2 right-2 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity bg-slate-800 rounded-full p-1">
                    <button 
                      className="text-slate-400 hover:text-slate-200 focus:text-slate-200 transition-colors p-1"
                      aria-label={`Copy message ${index + 1}`}
                      title="Copy message content"
                      onClick={() => {
                        navigator.clipboard.writeText(message.content);
                        info('Copied', 'Message copied to clipboard');
                      }}
                    >
                      <EyeIcon className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start slide-up">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-teal-500 to-emerald-500 flex items-center justify-center">
                  <CpuChipIcon className="w-5 h-5 text-white animate-pulse" />
                </div>
                <div className="chat-bubble assistant">
                  <div className="flex items-center gap-2">
                    <span>Thinking</span>
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* File Previews */}
        {uploadedFiles.length > 0 && (
          <div className="mb-4 space-y-2">
            <h3 className="text-sm font-medium text-slate-400">Uploaded Files:</h3>
            <div className="flex flex-wrap gap-2">
              {uploadedFiles.map((filePreview) => (
                <div
                  key={filePreview.id}
                  className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 flex items-center gap-3 min-w-0"
                >
                  <DocumentArrowUpIcon className="w-5 h-5 text-purple-400 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-200 truncate">
                      {filePreview.file.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatFileSize(filePreview.file.size)}
                    </p>
                  </div>
                  <button
                    onClick={() => removeFile(filePreview.id)}
                    className="text-slate-400 hover:text-red-400 transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* URL Previews */}
        {urlPreviews.length > 0 && (
          <div className="mb-4 space-y-2">
            <h3 className="text-sm font-medium text-slate-400">Added Links:</h3>
            <div className="space-y-2">
              {urlPreviews.map((urlPreview) => (
                <div
                  key={urlPreview.id}
                  className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 flex items-center gap-3"
                >
                  {urlPreview.favicon ? (
                    <img
                      src={urlPreview.favicon}
                      alt=""
                      className="w-5 h-5 flex-shrink-0"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <GlobeAltIcon className="w-5 h-5 text-teal-400 flex-shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-200 truncate">
                      {urlPreview.title}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {urlPreview.url}
                    </p>
                  </div>
                  <button
                    onClick={() => removeUrl(urlPreview.id)}
                    className="text-slate-400 hover:text-red-400 transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}        {/* Input Area */}
        <div className="card space-y-4 relative overflow-hidden">
          {/* Animated Background */}
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-0 left-0 w-32 h-32 bg-purple-500/10 rounded-full blur-xl animate-pulse"></div>
            <div className="absolute bottom-0 right-0 w-24 h-24 bg-teal-500/10 rounded-full blur-xl animate-pulse" style={{animationDelay: '1s'}}></div>
          </div>
          
          <div className="relative z-10 space-y-4">
            {/* File Upload Zone */}
            <div
              className={`file-upload-zone group ${isDragOver ? 'drag-over glow-effect' : ''}`}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="transition-transform group-hover:scale-110">
                <DocumentArrowUpIcon className="w-8 h-8 text-purple-400 mx-auto mb-2" />
              </div>
              <p className="text-slate-300 font-medium">
                {isDragOver ? '✨ Drop files here' : '📁 Drag & drop files or click to browse'}
              </p>
              <p className="text-slate-500 text-sm mt-1">
                PDF, Word, Excel, PowerPoint, and text files supported
              </p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={(e) => e.target.files && addFiles(Array.from(e.target.files))}
                className="hidden"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md"
              />
            </div>

            {/* URL Input with Enhanced Design */}
            <div className="url-input-container group">
              <div className="flex items-center gap-3">
                <LinkIcon className="w-5 h-5 text-teal-400 flex-shrink-0 transition-transform group-focus-within:scale-110" />
                <input
                  type="url"
                  placeholder="🔗 Paste SharePoint, Google Drive, or any web link..."
                  value={urlInputValue}
                  onChange={(e) => setUrlInputValue(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addUrl()}
                  className="flex-1 bg-transparent border-none outline-none text-slate-200 placeholder-slate-500"
                />
                <button
                  onClick={addUrl}
                  disabled={!urlInputValue.trim()}
                  className="btn-secondary px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:glow-effect-teal transition-all"
                >
                  Add Link
                </button>
              </div>
            </div>

            {/* Message Input with Enhanced Features */}
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="✨ Ask me anything about your documents..."
                  className="input-field resize-none w-full min-h-[3rem] max-h-32 pr-12"
                  rows={1}
                  style={{
                    height: 'auto',
                    minHeight: '3rem'
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 128) + 'px';
                  }}
                />
                
                {/* Character counter for long messages */}
                {inputValue.length > 100 && (
                  <div className="absolute bottom-2 right-2 text-xs text-slate-500">
                    {inputValue.length}/1000
                  </div>
                )}
              </div>
              
              <button
                onClick={handleSendMessage}
                disabled={isLoading || (!inputValue.trim() && uploadedFiles.length === 0 && urlPreviews.length === 0)}
                className="btn-primary px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed glow-effect group relative overflow-hidden"
              >
                <div className="flex items-center gap-2">
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Sending...</span>
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                      <span>Send</span>
                    </>
                  )}
                </div>
              </button>
            </div>
            
            {/* Quick Tips */}
            <div className="text-xs text-slate-500 text-center space-y-1">
              <p>💡 Press <kbd className="px-1 py-0.5 bg-slate-700 rounded text-slate-300">Enter</kbd> to send, <kbd className="px-1 py-0.5 bg-slate-700 rounded text-slate-300">Shift+Enter</kbd> for new line</p>
              <p>🎯 Upload documents or paste links for context-aware conversations</p>
            </div>
          </div>
        </div>
      </div>      {/* Drag Overlay */}
      {isDragOver && (
        <div className="fixed inset-0 bg-purple-900/20 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800/90 border-2 border-dashed border-purple-400 rounded-2xl p-8 text-center">
            <DocumentArrowUpIcon className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <p className="text-xl font-semibold text-slate-200 mb-2">Drop files here</p>
            <p className="text-slate-400">Release to upload your documents</p>
          </div>
        </div>
      )}      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal 
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
          onLogin={login}
          isLoading={authLoading}
          error={authError}
        />
      )}      {/* Document Manager */}
      {showDocumentManager && (
        <ErrorBoundary>
          <DocumentManager
            isOpen={showDocumentManager}
            onClose={() => setShowDocumentManager(false)}
          />
        </ErrorBoundary>
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <ErrorBoundary>
          <SettingsModal
            isOpen={showSettingsModal}
            onClose={() => setShowSettingsModal(false)}
          />
        </ErrorBoundary>
      )}

      {/* Chat Search Modal */}
      {showChatSearch && (
        <ErrorBoundary>
          <ChatSearch
            isOpen={showChatSearch}
            onClose={() => setShowChatSearch(false)}
            messages={messages}
            onMessageSelect={handleMessageSelect}
          />
        </ErrorBoundary>
      )}      {/* Quick Actions Panel */}
      {showQuickActions && (
        <ErrorBoundary>
          <QuickActionsPanel
            isOpen={showQuickActions}
            onClose={() => setShowQuickActions(false)}
            onFileUpload={() => fileInputRef.current?.click()}
            onUrlAdd={() => (document.querySelector('input[placeholder*="paste"]') as HTMLInputElement)?.focus()}
            onSearch={() => setShowChatSearch(true)}
            onClearChat={handleClearChat}
            onExportChat={handleExportChat}
            onNewChat={handleNewChat}
          />
        </ErrorBoundary>
      )}      {/* Keyboard Shortcuts Modal */}
      <KeyboardShortcutsModal
        isOpen={showKeyboardShortcuts}
        onClose={() => setShowKeyboardShortcuts(false)}
      />

      {/* Performance Monitor */}
      <PerformanceMonitor
        messageCount={messages.length}
        isVisible={showPerformanceMonitor}
        onToggle={() => setShowPerformanceMonitor(!showPerformanceMonitor)}
      />

      {/* Notification Container */}
      <NotificationContainer
        notifications={notifications}
        onRemove={removeNotification}
      />
    </div>
  );
};

export default ModernChatInterface;
