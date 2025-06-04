import React, { useState } from 'react';
import { Globe, Link, Plus, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface WebSource {
  id: string;
  url: string;
  title?: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  error?: string;
}

interface WebImporterProps {
  onUrlImport?: (url: string) => Promise<{ title: string; content: string }>;
}

const WebImporter: React.FC<WebImporterProps> = ({ onUrlImport }) => {
  const [sources, setSources] = useState<WebSource[]>([]);
  const [newUrl, setNewUrl] = useState('');

  const isValidUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleAddUrl = async () => {
    if (!newUrl.trim()) return;

    let formattedUrl = newUrl.trim();
    if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
      formattedUrl = 'https://' + formattedUrl;
    }

    if (!isValidUrl(formattedUrl)) {
      alert('Veuillez entrer une URL valide');
      return;
    }

    // Check if URL already exists
    if (sources.some(source => source.url === formattedUrl)) {
      alert('Cette URL a déjà été ajoutée');
      return;
    }

    const newSource: WebSource = {
      id: Date.now().toString(),
      url: formattedUrl,
      status: 'pending'
    };

    setSources(prev => [...prev, newSource]);
    setNewUrl('');

    // Start importing
    await importUrl(newSource);
  };

  const importUrl = async (source: WebSource) => {
    setSources(prev => prev.map(s => 
      s.id === source.id ? { ...s, status: 'loading' } : s
    ));

    try {
      let result = { title: source.url, content: '' };
      
      if (onUrlImport) {
        result = await onUrlImport(source.url);
      } else {
        // Simulate import
        await new Promise(resolve => setTimeout(resolve, 2000));
        result.title = `Contenu de ${new URL(source.url).hostname}`;
      }

      setSources(prev => prev.map(s => 
        s.id === source.id ? { 
          ...s, 
          status: 'success', 
          title: result.title 
        } : s
      ));
    } catch (error) {
      setSources(prev => prev.map(s => 
        s.id === source.id ? { 
          ...s, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Erreur d\'import'
        } : s
      ));
    }
  };

  const removeSource = (id: string) => {
    setSources(prev => prev.filter(s => s.id !== id));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddUrl();
    }
  };

  const getDomainFromUrl = (url: string) => {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Globe className="w-5 h-5 text-green-500" />
        Importer des sites web
      </h3>

      {/* URL Input */}
      <div className="mb-6">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="https://example.com ou example.com"
              className="w-full p-3 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <Link className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          </div>
          <button
            onClick={handleAddUrl}
            disabled={!newUrl.trim()}
            className="px-4 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg hover:from-green-600 hover:to-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        
        <p className="text-xs text-gray-500 mt-2">
          Ajoutez des URLs de sites web, articles de blog, documentation, etc.
        </p>
      </div>

      {/* Sources List */}
      {sources.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Sources web ({sources.length})
          </h4>
          
          <div className="space-y-3">
            {sources.map((source) => (
              <div key={source.id} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-teal-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Globe className="w-5 h-5 text-white" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h5 className="text-sm font-medium text-gray-800 truncate">
                          {source.title || getDomainFromUrl(source.url)}
                        </h5>
                        
                        {source.status === 'loading' && (
                          <Loader2 className="w-4 h-4 animate-spin text-green-500 flex-shrink-0" />
                        )}
                        {source.status === 'success' && (
                          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                        )}
                        {source.status === 'error' && (
                          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                        )}
                      </div>
                      
                      <p className="text-xs text-gray-500 truncate mb-1">
                        {source.url}
                      </p>
                      
                      {source.status === 'loading' && (
                        <p className="text-xs text-green-600">
                          Import en cours...
                        </p>
                      )}
                      
                      {source.status === 'success' && (
                        <p className="text-xs text-green-600">
                          Contenu importé avec succès
                        </p>
                      )}
                      
                      {source.status === 'error' && source.error && (
                        <p className="text-xs text-red-600">
                          {source.error}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => removeSource(source.id)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 ml-2"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {sources.length === 0 && (
        <div className="text-center py-8">
          <Globe className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">
            Aucune source web ajoutée
          </p>
          <p className="text-gray-400 text-xs mt-1">
            Ajoutez des URLs pour importer du contenu web
          </p>
        </div>
      )}
    </div>
  );
};

export default WebImporter;
