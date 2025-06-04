import React, { useState, useEffect } from 'react';
import { 
  DocumentIcon, 
  TrashIcon, 
  EyeIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  FolderIcon
} from '@heroicons/react/24/outline';
import { useSimpleAuth } from '../hooks/useSimpleAuth';
import '../styles/modern-dark-theme.css';

interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  upload_date: string;
  document_type: string;
  status: string;
}

interface DocumentManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({ isOpen, onClose }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { isAuthenticated, getAuthHeaders } = useSimpleAuth();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8003';

  useEffect(() => {
    if (isOpen && isAuthenticated) {
      loadDocuments();
    }
  }, [isOpen, isAuthenticated]);

  const loadDocuments = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const authHeaders = getAuthHeaders();
      const response = await fetch(`${API_BASE}/api/v1/documents`, {
        headers: {
          'Content-Type': 'application/json',
          ...(authHeaders.Authorization ? { Authorization: authHeaders.Authorization } : {}),
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      } else if (response.status === 401) {
        setError('Authentication required');
      } else {
        setError('Failed to load documents');
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      setError('Network error while loading documents');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      const authHeaders = getAuthHeaders();
      const response = await fetch(`${API_BASE}/api/v1/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          ...(authHeaders.Authorization ? { Authorization: authHeaders.Authorization } : {}),
        },
      });

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      } else {
        setError('Failed to delete document');
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      setError('Network error while deleting document');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  const filteredDocuments = documents.filter(doc =>
    doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.document_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gradient-to-br from-slate-900/95 to-purple-900/95 backdrop-blur-xl border border-white/10 rounded-2xl w-full max-w-4xl max-h-[80vh] mx-4 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FolderIcon className="w-6 h-6 text-purple-400" />
              <h2 className="text-2xl font-bold text-gradient">Document Manager</h2>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 transition-colors p-2 hover:bg-slate-800/50 rounded-lg"
            >
              ✕
            </button>
          </div>

          {/* Search Bar */}
          <div className="mt-4 relative">
            <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-900/50 border border-red-500/50 rounded-lg p-4 mb-4">
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-slate-400">Loading documents...</p>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-8">
              <DocumentIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">
                {searchTerm ? 'No documents match your search' : 'No documents uploaded yet'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 hover:bg-slate-800/50 transition-all group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <DocumentIcon className="w-5 h-5 text-purple-400 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium text-slate-200 truncate">
                          {doc.original_filename}
                        </h3>
                        <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                          <span>{formatFileSize(doc.file_size)}</span>
                          <span>•</span>
                          <span>{formatDate(doc.upload_date)}</span>
                          <span>•</span>
                          <span className="capitalize">{doc.document_type}</span>
                          <span>•</span>
                          <span className={`capitalize ${
                            doc.status === 'processed' ? 'text-green-400' : 
                            doc.status === 'processing' ? 'text-yellow-400' : 
                            'text-red-400'
                          }`}>
                            {doc.status}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="View"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-slate-400 hover:text-green-400 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="Download"
                      >
                        <ArrowDownTrayIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deleteDocument(doc.id)}
                        className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-white/10">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>{filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''}</span>
            <button
              onClick={loadDocuments}
              className="btn-secondary px-3 py-1 text-xs"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentManager;
