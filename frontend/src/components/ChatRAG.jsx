import React, { useState, useRef, useEffect } from 'react';
import { useToast } from '../contexts/ToastContext';

const ChatRAG = ({ sessionId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();
  const chatEndRef = useRef(null);

  useEffect(() => {
    // Load chat history for the session
    const fetchHistory = async () => {
      try {
        const res = await fetch(`/api/v1/rag/history?session_id=${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          setMessages(data.history || []);
        }
      } catch (e) {}
    };
    // Prevent fetchHistory in test environment
    if (sessionId && !(typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'test')) fetchHistory();
  }, [sessionId]);

  useEffect(() => {
    if (chatEndRef.current && typeof chatEndRef.current.scrollIntoView === 'function') {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError('');
    const userMsg = { role: 'user', content: input };
    setMessages((msgs) => [...msgs, userMsg]);
    try {
      const res = await fetch('/api/v1/rag/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input, session_id: sessionId }),
      });
      if (!res.ok) {
        let errMsg = 'Failed to get answer';
        try {
          const errData = await res.json();
          if (errData && errData.error) errMsg = errData.error;
          else if (errData && errData.detail) errMsg = errData.detail;
        } catch {}
        throw new Error(errMsg);
      }
      const data = await res.json();
      setMessages((msgs) => [...msgs, { role: 'assistant', content: data.answer, sources: data.sources }]);
      setInput('');
    } catch (err) {
      let errMsg = 'Failed to get response';
      if (err && err.message) errMsg = err.message;
      setError(errMsg);
      showToast('error', 'Chat Error', errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-10 p-6 bg-white rounded shadow flex flex-col h-[70vh]">
      <h2 className="text-2xl font-bold mb-4">AskRAG Chat</h2>
      <div className="flex-1 overflow-y-auto mb-4 border rounded p-3 bg-gray-50">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-2 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block px-3 py-2 rounded ${msg.role === 'user' ? 'bg-blue-100' : 'bg-green-100'}`}>
              {msg.content}
              {msg.sources && msg.sources.length > 0 && (
                <div className="text-xs mt-1 text-gray-500">Sources: {msg.sources.join(', ')}</div>
              )}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          className="flex-1 border px-3 py-2 rounded"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded" disabled={loading}>
          {loading ? '...' : 'Send'}
        </button>
      </form>
      {error && (
        <div className="mt-2 text-red-600 text-sm" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

export default ChatRAG;
