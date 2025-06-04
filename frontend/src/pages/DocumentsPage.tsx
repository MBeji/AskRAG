import { useState, useCallback } from 'react';
import { 
  CloudArrowUpIcon, 
  DocumentTextIcon, 
  TrashIcon,
  EyeIcon 
} from '@heroicons/react/24/outline';

interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'processing' | 'completed' | 'error';
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  }, []);

  const handleFiles = async (files: File[]) => {
    setIsUploading(true);
    
    for (const file of files) {
      const newDoc: Document = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        uploadedAt: new Date(),
        status: 'processing',
      };

      setDocuments(prev => [...prev, newDoc]);

      // Simulate upload and processing
      setTimeout(() => {
        setDocuments(prev => 
          prev.map(doc => 
            doc.id === newDoc.id 
              ? { ...doc, status: 'completed' as const }
              : doc
          )
        );
      }, 2000);
    }
    
    setIsUploading(false);
  };

  const handleDeleteDocument = (id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
        <p className="text-gray-600 mt-2">
          Upload and manage your documents for AI-powered question answering
        </p>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200 ${
          isDragOver
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Upload Documents
        </h3>
        <p className="text-gray-600 mb-4">
          Drag and drop files here, or click to select files
        </p>
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
          accept=".pdf,.doc,.docx,.txt,.md"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 cursor-pointer transition-colors duration-200"
        >
          Select Files
        </label>
        <p className="text-sm text-gray-500 mt-2">
          Supported formats: PDF, DOC, DOCX, TXT, MD
        </p>
      </div>

      {/* Documents List */}
      {documents.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Uploaded Documents ({documents.length})
          </h2>
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <li key={doc.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <DocumentTextIcon className="w-8 h-8 text-gray-400" />
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          {doc.name}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(doc.size)} • Uploaded {doc.uploadedAt.toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}
                      >
                        {doc.status === 'processing' && (
                          <div className="flex items-center">
                            <div className="w-3 h-3 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin mr-1"></div>
                            Processing
                          </div>
                        )}
                        {doc.status === 'completed' && 'Ready'}
                        {doc.status === 'error' && 'Error'}
                      </span>
                      {doc.status === 'completed' && (
                        <button
                          className="p-1 text-gray-400 hover:text-gray-600"
                          title="View document"
                        >
                          <EyeIcon className="w-5 h-5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete document"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Empty State */}
      {documents.length === 0 && !isUploading && (
        <div className="text-center py-12">
          <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No documents uploaded yet
          </h3>
          <p className="text-gray-600">
            Upload your first document to start asking questions about its content.
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage;
