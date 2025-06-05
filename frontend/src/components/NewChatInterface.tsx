import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext'; // Import useChat
// askRAG and response types are now handled by ChatContext's sendMessage
// import { askRAG, RAGQueryResponse, SearchResultItem } from '../services/api';
import { ChatMessage, SearchResultItem } from '../types'; // Import common types

const NewChatInterface: React.FC = () => {
  // Local state for input value
  const [inputValue, setInputValue] = useState('');

  // Get state and functions from ChatContext
  const {
    currentSession,
    sendMessage,
    isLoadingMessages // Use this for loading state from context
  } = useChat();
  const { isAuthenticated } = useAuth();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Display messages from currentSession managed by ChatContext
  const messagesToDisplay = currentSession?.messages || [];
  useEffect(scrollToBottom, [messagesToDisplay]);


  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    if (!isAuthenticated) {
      alert("Please log in to use the chat.");
      return;
    }

    const currentInput = inputValue;
    setInputValue(''); // Clear input immediately (optimistic)

    try {
      await sendMessage(currentInput); // sendMessage now handles API call and state updates in context
    } catch (error) {
      // Error handling might be done in context, or display a generic error here if needed
      console.error("Error sending message via context:", error);
      // Optionally, add a temporary error message to local display if context doesn't handle it
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', borderLeft: '1px solid #eee' /* Ensure full height within its column */ }}>
      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '20px' }}> {/* Increased padding */}
        {messagesToDisplay.length === 0 && !isLoadingMessages && (
          <div style={{textAlign: 'center', color: '#aaa', marginTop: '50px'}}>
            <p>Select a session or start a new chat.</p>
            <p>Your messages will appear here.</p>
          </div>
        )}
        {messagesToDisplay.map((msg: ChatMessage) => ( // Use ChatMessage type from context/types
          <div key={msg.message_id} style={{ marginBottom: '12px', textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
            <div
              style={{
                display: 'inline-block',
                padding: '8px 12px',
                borderRadius: '15px',
                backgroundColor: msg.sender === 'user' ? '#007bff' : '#e9ecef',
                color: msg.sender === 'user' ? 'white' : 'black',
                maxWidth: '70%',
                wordWrap: 'break-word'
              }}
            >
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.text}</p>
            </div> {/* End of main message bubble content */}

            {/* Enhanced Source Display for Bot Messages */}
            {msg.sender === 'bot' && msg.sources && msg.sources.length > 0 && (
              <div style={{
                marginTop: '12px',
                paddingTop: '8px',
                borderTop: '1px solid rgba(255, 255, 255, 0.2)' // Adjusted for a potentially dark theme from inline styles
              }}>
                <h4 style={{ fontSize: '0.9em', fontWeight: 'bold', marginBottom: '5px', color: msg.sender === 'user' ? 'white' : 'black' }}>
                  Sources:
                </h4>
                <div style={{ maxHeight: '150px', overflowY: 'auto', fontSize: '0.8em', paddingRight: '5px' }}>
                  {msg.sources.map((source, index) => (
                    <div key={index} style={{
                      marginBottom: '8px',
                      padding: '8px',
                      border: '1px solid rgba(255, 255, 255, 0.1)', // Adjusted for dark theme
                      borderRadius: '4px',
                      backgroundColor: 'rgba(0,0,0,0.1)' // Slight background for source items
                    }}>
                      <p style={{ fontWeight: 'bold', margin: '0 0 4px 0', color: msg.sender === 'user' ? 'white' : 'black' }}>
                        {index + 1}. {source.source_filename}
                      </p>
                      <p style={{ fontSize: '0.9em', margin: '0 0 4px 0', fontStyle: 'italic', color: msg.sender === 'user' ? '#eee' : '#333' }}>
                        "{source.chunk_text.substring(0, 150)}..."
                      </p>
                      <p style={{ fontSize: '0.85em', margin: '0', color: msg.sender === 'user' ? '#ccc' : '#555' }}>
                        Chunk: {source.chunk_index} | Relevance: {source.score !== undefined ? source.score.toFixed(2) : 'N/A'}
                        {/* Optional: Doc ID: {source.document_id} */}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Timestamp and sender info, moved outside the main content + sources block */}
            <p style={{ fontSize: '0.75em', color: '#666', margin: '2px 0',
                        textAlign: msg.sender === 'user' ? 'right' : 'left',
                        width: '100%' // Ensure it takes full width of the outer flex item
            }}>
              {msg.sender} - {new Date().toLocaleTimeString()}
            </p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      {isLoading && <div style={{padding: '5px', textAlign: 'center', fontStyle: 'italic'}}>Bot is thinking...</div>}
      <div style={{ display: 'flex', padding: '10px', borderTop: '1px solid #ccc' }}>
        <textarea
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder={isAuthenticated ? "Type your message..." : "Please log in to chat"}
          disabled={!isAuthenticated || isLoading}
          style={{ flexGrow: 1, marginRight: '10px', padding: '8px', borderRadius: '5px', border: '1px solid #ccc', resize: 'none' }}
          rows={2}
        />
        <button
          onClick={handleSendMessage}
          disabled={!isAuthenticated || isLoading || !inputValue.trim()}
          style={{ padding: '10px 15px', borderRadius: '5px', border: 'none', backgroundColor: '#007bff', color: 'white', cursor: 'pointer' }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default NewChatInterface;
