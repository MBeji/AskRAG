import { useState } from 'react';
import { 
  KeyIcon, 
  ServerIcon, 
  AdjustmentsHorizontalIcon 
} from '@heroicons/react/24/outline';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState({
    apiKey: '',
    apiUrl: 'http://localhost:8000',
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 1000,
    chunkSize: 1000,
    chunkOverlap: 200,
    topK: 5,
  });

  const [activeTab, setActiveTab] = useState<'api' | 'model' | 'rag'>('api');

  const handleSettingChange = (key: string, value: string | number) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSaveSettings = () => {
    // Save to localStorage or send to backend
    localStorage.setItem('askrag-settings', JSON.stringify(settings));
    alert('Settings saved successfully!');
  };

  const tabs = [
    { id: 'api', name: 'API Configuration', icon: KeyIcon },
    { id: 'model', name: 'Model Settings', icon: ServerIcon },
    { id: 'rag', name: 'RAG Parameters', icon: AdjustmentsHorizontalIcon },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">
          Configure your AskRAG application settings
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-5 h-5 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="max-w-2xl">
        {/* API Configuration */}
        {activeTab === 'api' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                value={settings.apiKey}
                onChange={(e) => handleSettingChange('apiKey', e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">
                Your OpenAI API key for accessing GPT models
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Backend API URL
              </label>
              <input
                type="url"
                value={settings.apiUrl}
                onChange={(e) => handleSettingChange('apiUrl', e.target.value)}
                placeholder="http://localhost:8000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">
                URL of your AskRAG backend API
              </p>
            </div>
          </div>
        )}

        {/* Model Settings */}
        {activeTab === 'model' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Model
              </label>
              <select
                value={settings.model}
                onChange={(e) => handleSettingChange('model', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              >
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                Choose the AI model for generating responses
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature: {settings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-1">
                Controls randomness in responses (0 = deterministic, 2 = very creative)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                min="100"
                max="4000"
                value={settings.maxTokens}
                onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">
                Maximum number of tokens in the response
              </p>
            </div>
          </div>
        )}

        {/* RAG Parameters */}
        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chunk Size
              </label>
              <input
                type="number"
                min="200"
                max="2000"
                value={settings.chunkSize}
                onChange={(e) => handleSettingChange('chunkSize', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">
                Size of text chunks for document processing
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chunk Overlap
              </label>
              <input
                type="number"
                min="0"
                max="500"
                value={settings.chunkOverlap}
                onChange={(e) => handleSettingChange('chunkOverlap', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">
                Overlap between consecutive chunks
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Top K Results
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={settings.topK}
                onChange={(e) => handleSettingChange('topK', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <p className="text-sm text-gray-500 mt-1">
                Number of most relevant chunks to retrieve for each query
              </p>
            </div>
          </div>
        )}

        {/* Save Button */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={handleSaveSettings}
            className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors duration-200"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
