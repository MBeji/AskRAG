import React, { useState } from 'react';
import { useToast } from '../contexts/ToastContext';

const DocumentUpload = ({ onUpload }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { showToast } = useToast();

  const handleFileChange = (e) => {
    setFile(e.target.files);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || file.length === 0) {
      setError('Please select at least one file.');
      return;
    }    // Support PDF, DOCX, TXT, MD, HTML
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown', 'text/html'];
    let allSuccess = true;
    for (let i = 0; i < file.length; i++) {
      const f = file[i];
      if (!allowed.includes(f.type) && !/\.(pdf|docx|txt|md|html)$/i.test(f.name)) {
        const errorMsg = `Format non supporté pour ${f.name}. Formats acceptés: PDF, DOCX, TXT, MD, HTML`;
        setError(errorMsg);
        showToast('error', 'Invalid File Format', errorMsg);
        allSuccess = false;
        continue;
      }
      setLoading(true);
      setError('');
      setSuccess('');
      const formData = new FormData();
      formData.append('file', f);
      try {
        const response = await fetch('/api/v1/documents/upload', {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Upload failed');
        }
        showToast('success', 'Document Uploaded', `${f.name} has been successfully uploaded and processed.`);
        if (onUpload) onUpload(f.name);
      } catch (err) {
        setError(err.message);
        showToast('error', 'Upload Failed', err.message);
        allSuccess = false;
      } finally {
        setLoading(false);
      }
    }
    if (allSuccess) {
      setSuccess('Tous les fichiers ont été uploadés avec succès !');
      setFile(null);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Upload Document</h2>
      <div className="mb-2 text-sm text-gray-600">Formats supportés : PDF, DOCX, TXT, MD, HTML</div>
      <form onSubmit={handleSubmit}>
        <input type="file" accept=".pdf,.docx,.txt,.md,.html" onChange={handleFileChange} className="mb-4" multiple />
        {error && <div className="text-red-500 mb-2">{error}</div>}
        {success && <div className="text-green-600 mb-2">{success}</div>}
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded" disabled={loading}>
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  );
};

export default DocumentUpload;
