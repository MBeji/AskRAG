import React, { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface FileItem {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

interface FileUploaderProps {
  onFileUpload?: (files: File[]) => Promise<void>;
  acceptedTypes?: string[];
  maxFiles?: number;
  maxFileSize?: number; // in MB
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onFileUpload,
  acceptedTypes = ['.pdf', '.doc', '.docx', '.txt', '.md'],
  maxFiles = 10,
  maxFileSize = 10
}) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

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
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    handleFiles(selectedFiles);
    // Reset input value to allow selecting same file again
    e.target.value = '';
  }, []);

  const handleFiles = useCallback((newFiles: File[]) => {
    const validFiles = newFiles.filter(file => {
      // Check file type
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedTypes.includes(extension)) {
        return false;
      }
      
      // Check file size
      if (file.size > maxFileSize * 1024 * 1024) {
        return false;
      }
      
      return true;
    });

    if (files.length + validFiles.length > maxFiles) {
      alert(`Vous ne pouvez uploader que ${maxFiles} fichiers maximum.`);
      return;
    }

    const fileItems: FileItem[] = validFiles.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      status: 'pending',
      progress: 0
    }));

    setFiles(prev => [...prev, ...fileItems]);
    
    // Start upload simulation
    fileItems.forEach(fileItem => {
      uploadFile(fileItem);
    });
  }, [files.length, acceptedTypes, maxFiles, maxFileSize]);

  const uploadFile = async (fileItem: FileItem) => {
    setFiles(prev => prev.map(f => 
      f.id === fileItem.id ? { ...f, status: 'uploading' } : f
    ));

    try {
      // Simulate upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id ? { ...f, progress } : f
        ));
      }

      // Call the actual upload function if provided
      if (onFileUpload) {
        await onFileUpload([fileItem.file]);
      }

      setFiles(prev => prev.map(f => 
        f.id === fileItem.id ? { ...f, status: 'success', progress: 100 } : f
      ));
    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id ? { 
          ...f, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Erreur d\'upload'
        } : f
      ));
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Upload className="w-5 h-5 text-blue-500" />
        Importer des fichiers
      </h3>

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer ${
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <Upload className={`w-12 h-12 mx-auto mb-4 ${
          isDragOver ? 'text-blue-500' : 'text-gray-400'
        }`} />
        
        <p className="text-lg font-medium text-gray-700 mb-2">
          Glissez-déposez vos fichiers ici
        </p>
        
        <p className="text-sm text-gray-500 mb-4">
          ou cliquez pour sélectionner
        </p>
        
        <input
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />
        
        <label
          htmlFor="file-upload"
          className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 cursor-pointer transition-all duration-200"
        >
          <File className="w-4 h-4 mr-2" />
          Sélectionner des fichiers
        </label>
        
        <p className="text-xs text-gray-400 mt-4">
          Formats acceptés: {acceptedTypes.join(', ')} • Max {maxFileSize}MB par fichier
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Fichiers ({files.length}/{maxFiles})
          </h4>
          
          <div className="space-y-3">
            {files.map((fileItem) => (
              <div key={fileItem.id} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <File className="w-5 h-5 text-blue-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {fileItem.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(fileItem.file.size)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {fileItem.status === 'uploading' && (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                    )}
                    {fileItem.status === 'success' && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                    {fileItem.status === 'error' && (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    )}
                    
                    <button
                      onClick={() => removeFile(fileItem.id)}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {/* Progress Bar */}
                {fileItem.status === 'uploading' && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${fileItem.progress}%` }}
                    />
                  </div>
                )}
                
                {/* Error Message */}
                {fileItem.status === 'error' && fileItem.error && (
                  <p className="text-sm text-red-600 mt-1">{fileItem.error}</p>
                )}
                
                {/* Success Message */}
                {fileItem.status === 'success' && (
                  <p className="text-sm text-green-600 mt-1">
                    Fichier uploadé avec succès
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
