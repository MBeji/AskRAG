import React, { useState, useEffect, useCallback } from 'react';
import { DocumentTextIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import FileUploader from '../components/FileUploader'; // Import the FileUploader component
import { uploadDocument as apiUploadDocument, getDocuments as apiGetDocuments, deleteDocument as apiDeleteDocument } from '../services/api'; // Import API functions
import { DocumentOut } from '../schemas/document'; // Assuming DocumentOut is the correct schema from backend

// Use DocumentOut schema for the document type, or a custom frontend type if needed
// For now, let's use DocumentOut and adapt if necessary.
// interface Document extends DocumentOut {
//   // any frontend specific additions?
//   // For now, assume DocumentOut is sufficient.
// }

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [isLoading, setIsLoading] = useState(false); // For loading documents list
  const [error, setError] = useState<string | null>(null); // For displaying errors

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedDocs = await apiGetDocuments(); // API call
      setDocuments(fetchedDocs);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
      setError("Failed to load documents. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileUpload = async (filesToUpload: File[]): Promise<void> => {
    // This function will be passed to FileUploader's onFileUpload prop.
    // FileUploader itself will manage individual file progress and status display.
    // This function is responsible for the actual upload logic for each file.
    let anErrorOccurred = false;
    for (const file of filesToUpload) {
      try {
        // The FileUploader component will display its own progress for this file.
        // We just need to call the API.
        await apiUploadDocument(file);
        // Optionally, display a global success message or let FileUploader handle it.
      } catch (uploadError: any) {
        console.error(`Failed to upload ${file.name}:`, uploadError);
        anErrorOccurred = true;
        // Error for this specific file will be handled by FileUploader's UI.
        // We could collect errors here if needed for a summary.
      }
    }
    // After all uploads attempt, refresh the document list
    await fetchDocuments();
    if (anErrorOccurred) {
      // Optionally set a general error message if any file failed.
      // setError("Some files failed to upload. Please check details above.");
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      await apiDeleteDocument(documentId);
      // Refresh documents list after deletion
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    } catch (err) {
      console.error("Failed to delete document:", err);
      setError("Failed to delete document. Please try again.");
    }
  };

  // Helper to format file size (can be moved to a utils file)
  const formatFileSize = (bytes: number | undefined) => {
    if (bytes === undefined || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Helper for status color (can be moved to a utils file or defined within component)
  const getStatusColor = (status: string | undefined) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800'; // Assuming pending is like processing
      case 'processed': return 'bg-green-100 text-green-800'; // Matched to DocumentModel status
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
        <p className="text-gray-600 mt-2">
          Upload new documents and manage existing ones for AI-powered question answering.
        </p>
      </div>

      {/* FileUploader Component */}
      <FileUploader
        onFileUpload={handleFileUpload}
        // Max file size from settings (e.g., settings.MAX_UPLOAD_SIZE_MB if defined)
        // For now, using FileUploader's default or pass a value.
        // maxFileSize={10} // In MB, should match backend config eventually
        // acceptedTypes={['.pdf', '.txt', '.docx', '.md']} // Should match backend config
      />

      {error && (
        <div className="rounded-md bg-red-50 p-4 mt-4">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      {/* Documents List */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Uploaded Documents ({documents.length})
        </h2>
        {isLoading && <p>Loading documents...</p>}
        {!isLoading && documents.length === 0 && (
          <div className="text-center py-12">
            <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No documents uploaded yet
            </h3>
            <p className="text-gray-600">
              Upload your first document using the uploader above.
            </p>
          </div>
        )}
        {!isLoading && documents.length > 0 && (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <li key={doc.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <DocumentTextIcon className="w-8 h-8 text-gray-400" />
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          {doc.filename} {/* Changed from doc.name */}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(doc.file_size)} • Uploaded {new Date(doc.upload_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}
                      >
                        {/* Simplified status display - adapt as needed */}
                        {doc.status || 'Unknown'}
                      </span>
                      <button
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="View document (not implemented)"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </button>
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
        )}
      </div>
    </div>
  );
};

export default DocumentsPage;
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
