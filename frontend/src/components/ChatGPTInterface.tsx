import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Upload, Link, X, File, Globe, Plus, Paperclip } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  attachments?: Array<{
    type: 'file' | 'url';
    name: string;
    size?: string;
  }>;
}

interface ChatGPTInterface {
  onSendMessage?: (message: string, files?: File[], urls?: string[]) => Promise<string>;
}

const ChatGPTInterface: React.FC<ChatGPTInterface> = ({ onSendMessage }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Bonjour ! Je suis votre assistant AskRAG. Vous pouvez me poser des questions, importer des fichiers ou ajouter des liens web pour enrichir mes connaissances.",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [attachedUrls, setAttachedUrls] = useState<string[]>([]);
  const [urlInput, setUrlInput] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachedFiles(prev => [...prev, ...files]);
    setShowAttachMenu(false);
  };

  const handleAddUrl = () => {
    if (urlInput.trim()) {
      let formattedUrl = urlInput.trim();
      if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
        formattedUrl = 'https://' + formattedUrl;
      }
      setAttachedUrls(prev => [...prev, formattedUrl]);
      setUrlInput('');
      setShowAttachMenu(false);
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const removeUrl = (index: number) => {
    setAttachedUrls(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleSendMessage = async () => {
    if ((!inputMessage.trim() && attachedFiles.length === 0 && attachedUrls.length === 0) || isLoading) return;

    const attachments = [
      ...attachedFiles.map(file => ({
        type: 'file' as const,
        name: file.name,
        size: formatFileSize(file.size)
      })),
      ...attachedUrls.map(url => ({
        type: 'url' as const,
        name: url
      }))
    ];

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage || (attachments.length > 0 ? `J'ai ajouté ${attachments.length} fichier(s)/lien(s)` : ''),
      isUser: true,
      timestamp: new Date(),
      attachments: attachments.length > 0 ? attachments : undefined
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setAttachedFiles([]);
    setAttachedUrls([]);
    setIsLoading(true);

    try {
      let response = "Merci ! J'ai bien reçu votre message";
      
      if (attachments.length > 0) {
        response += ` et ${attachments.length} fichier(s)/lien(s). Je les ai analysés et ils sont maintenant disponibles pour répondre à vos questions.`;
      }
      
      if (onSendMessage) {
        response = await onSendMessage(inputMessage, attachedFiles, attachedUrls);
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response,
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Désolé, je rencontre une erreur technique. Veuillez réessayer.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-teal-500 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">AskRAG</h1>
              <p className="text-sm text-gray-500">Assistant IA pour vos documents</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex gap-4 ${message.isUser ? 'justify-end' : 'justify-start'}`}>
                {!message.isUser && (
                  <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-teal-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                
                <div className={`max-w-[70%] ${message.isUser ? 'order-2' : ''}`}>
                  <div className={`p-4 rounded-2xl ${
                    message.isUser
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.text}</p>
                    
                    {/* Attachments */}
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-300/30">
                        <div className="space-y-2">
                          {message.attachments.map((attachment, index) => (
                            <div key={index} className="flex items-center gap-2 text-xs">
                              {attachment.type === 'file' ? (
                                <>
                                  <File className="w-3 h-3" />
                                  <span>{attachment.name}</span>
                                  {attachment.size && <span className="opacity-70">({attachment.size})</span>}
                                </>
                              ) : (
                                <>
                                  <Globe className="w-3 h-3" />
                                  <span className="truncate">{attachment.name}</span>
                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className={`text-xs text-gray-500 mt-1 ${message.isUser ? 'text-right' : 'text-left'}`}>
                    {message.timestamp.toLocaleTimeString('fr-FR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>

                {message.isUser && (
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0 mt-1 order-1">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-teal-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 p-4 rounded-2xl">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-green-500" />
                    <span className="text-sm text-gray-600">En train d'analyser...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          {/* Attached Files and URLs */}
          {(attachedFiles.length > 0 || attachedUrls.length > 0) && (
            <div className="mb-3 p-3 bg-gray-50 rounded-lg">
              <div className="flex flex-wrap gap-2">
                {attachedFiles.map((file, index) => (
                  <div key={`file-${index}`} className="flex items-center gap-2 bg-white px-3 py-1 rounded-full text-sm border">
                    <File className="w-3 h-3 text-blue-500" />
                    <span className="truncate max-w-32">{file.name}</span>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
                {attachedUrls.map((url, index) => (
                  <div key={`url-${index}`} className="flex items-center gap-2 bg-white px-3 py-1 rounded-full text-sm border">
                    <Globe className="w-3 h-3 text-green-500" />
                    <span className="truncate max-w-32">{new URL(url).hostname}</span>
                    <button
                      onClick={() => removeUrl(index)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Attachment Menu */}
          {showAttachMenu && (
            <div className="mb-3 p-4 bg-gray-50 rounded-lg border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* File Upload */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Fichiers</h4>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt,.md"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full flex items-center gap-2 p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors"
                  >
                    <Upload className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Sélectionner des fichiers</span>
                  </button>
                </div>

                {/* URL Input */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Lien web</h4>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      placeholder="https://example.com"
                      className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-sm"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddUrl()}
                    />
                    <button
                      onClick={handleAddUrl}
                      disabled={!urlInput.trim()}
                      className="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Input */}
          <div className="flex gap-3 items-end">
            <button
              onClick={() => setShowAttachMenu(!showAttachMenu)}
              className={`p-3 rounded-lg transition-colors ${
                showAttachMenu 
                  ? 'bg-gray-200 text-gray-700' 
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Paperclip className="w-5 h-5" />
            </button>
            
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question ou ajoutez des fichiers/liens..."
                disabled={isLoading}
                rows={1}
                className="w-full p-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:opacity-50 resize-none"
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
              
              <button
                onClick={handleSendMessage}
                disabled={(!inputMessage.trim() && attachedFiles.length === 0 && attachedUrls.length === 0) || isLoading}
                className="absolute right-2 bottom-2 p-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            Appuyez sur Entrée pour envoyer, Maj+Entrée pour une nouvelle ligne
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatGPTInterface;
