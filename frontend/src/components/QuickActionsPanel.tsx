import React, { useState } from 'react';
import {
  CommandLineIcon,
  DocumentPlusIcon,
  LinkIcon,
  MagnifyingGlassIcon,
  BookmarkIcon,
  ClockIcon,
  SparklesIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  ShareIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import '../styles/modern-dark-theme.css';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  color: string;
  shortcut?: string;
  action: () => void;
  category: 'document' | 'chat' | 'search' | 'utility';
}

interface QuickActionsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onFileUpload: () => void;
  onUrlAdd: () => void;
  onSearch: () => void;
  onClearChat: () => void;
  onExportChat: () => void;
  onNewChat: () => void;
}

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({
  isOpen,
  onClose,
  onFileUpload,
  onUrlAdd,
  onSearch,
  onClearChat,
  onExportChat,
  onNewChat
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'document' | 'chat' | 'search' | 'utility'>('all');

  const quickActions: QuickAction[] = [
    {
      id: 'upload-file',
      title: 'Upload Document',
      description: 'Add files to your knowledge base',
      icon: DocumentPlusIcon,
      color: 'purple',
      shortcut: 'Ctrl+U',
      action: onFileUpload,
      category: 'document'
    },
    {
      id: 'add-url',
      title: 'Add Web Link',
      description: 'Import content from URLs',
      icon: LinkIcon,
      color: 'teal',
      shortcut: 'Ctrl+L',
      action: onUrlAdd,
      category: 'document'
    },
    {
      id: 'search-chat',
      title: 'Search History',
      description: 'Find previous conversations',
      icon: MagnifyingGlassIcon,
      color: 'blue',
      shortcut: 'Ctrl+F',
      action: onSearch,
      category: 'search'
    },
    {
      id: 'new-chat',
      title: 'New Conversation',
      description: 'Start a fresh chat session',
      icon: ChatBubbleLeftRightIcon,
      color: 'green',
      shortcut: 'Ctrl+N',
      action: onNewChat,
      category: 'chat'
    },
    {
      id: 'export-chat',
      title: 'Export Chat',
      description: 'Download conversation history',
      icon: ShareIcon,
      color: 'orange',
      shortcut: 'Ctrl+E',
      action: onExportChat,
      category: 'utility'
    },
    {
      id: 'clear-chat',
      title: 'Clear Messages',
      description: 'Remove all messages',
      icon: ArrowPathIcon,
      color: 'red',
      action: onClearChat,
      category: 'utility'
    },
    {
      id: 'bookmark',
      title: 'Bookmark Chat',
      description: 'Save important conversations',
      icon: BookmarkIcon,
      color: 'yellow',
      action: () => console.log('Bookmark chat'),
      category: 'utility'
    },
    {
      id: 'recent-files',
      title: 'Recent Documents',
      description: 'Quick access to recent uploads',
      icon: ClockIcon,
      color: 'indigo',
      action: () => console.log('Show recent files'),
      category: 'document'
    },
    {
      id: 'templates',
      title: 'Message Templates',
      description: 'Use predefined prompts',
      icon: DocumentDuplicateIcon,
      color: 'pink',
      action: () => console.log('Show templates'),
      category: 'chat'
    },
    {
      id: 'smart-suggestions',
      title: 'Smart Suggestions',
      description: 'AI-powered action recommendations',
      icon: SparklesIcon,
      color: 'violet',
      action: () => console.log('Show suggestions'),
      category: 'chat'
    },
    {
      id: 'collaboration',
      title: 'Share Session',
      description: 'Collaborate with team members',
      icon: UserGroupIcon,
      color: 'cyan',
      action: () => console.log('Share session'),
      category: 'utility'
    },
    {
      id: 'feedback',
      title: 'Send Feedback',
      description: 'Help us improve AskRAG',
      icon: HeartIcon,
      color: 'rose',
      action: () => console.log('Send feedback'),
      category: 'utility'
    }
  ];

  const categories = [
    { id: 'all', label: 'All Actions', icon: CommandLineIcon },
    { id: 'document', label: 'Documents', icon: DocumentPlusIcon },
    { id: 'chat', label: 'Chat', icon: ChatBubbleLeftRightIcon },
    { id: 'search', label: 'Search', icon: MagnifyingGlassIcon },
    { id: 'utility', label: 'Utilities', icon: SparklesIcon }
  ];

  const filteredActions = quickActions.filter(action => {
    const matchesCategory = selectedCategory === 'all' || action.category === selectedCategory;
    const matchesSearch = searchTerm === '' || 
      action.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      action.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesCategory && matchesSearch;
  });

  const getColorClasses = (color: string) => {
    const colors: Record<string, string> = {
      purple: 'from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700',
      teal: 'from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700',
      blue: 'from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700',
      green: 'from-green-500 to-green-600 hover:from-green-600 hover:to-green-700',
      orange: 'from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700',
      red: 'from-red-500 to-red-600 hover:from-red-600 hover:to-red-700',
      yellow: 'from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700',
      indigo: 'from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700',
      pink: 'from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700',
      violet: 'from-violet-500 to-violet-600 hover:from-violet-600 hover:to-violet-700',
      cyan: 'from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700',
      rose: 'from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700'
    };
    return colors[color] || colors.purple;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-teal-500 rounded-lg flex items-center justify-center">
              <CommandLineIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-200">Quick Actions</h2>
              <p className="text-sm text-slate-400">Fast access to common operations</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors p-2 hover:bg-slate-800/50 rounded-lg"
          >
            ✕
          </button>
        </div>

        {/* Search and Categories */}
        <div className="p-6 border-b border-slate-700 space-y-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search actions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Categories */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  selectedCategory === category.id
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-600 hover:bg-slate-700/50 hover:text-slate-300'
                }`}
              >
                <category.icon className="w-4 h-4" />
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Actions Grid */}
        <div className="p-6 max-h-[50vh] overflow-y-auto">
          {filteredActions.length === 0 ? (
            <div className="text-center py-12">
              <CommandLineIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">No actions found</h3>
              <p className="text-slate-500">Try adjusting your search or category filter</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredActions.map((action) => (
                <button
                  key={action.id}
                  onClick={() => {
                    action.action();
                    onClose();
                  }}
                  className={`group relative bg-gradient-to-r ${getColorClasses(action.color)} rounded-xl p-6 text-left transition-all transform hover:scale-105 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    {action.shortcut && (
                      <div className="text-xs bg-white/20 text-white px-2 py-1 rounded-full font-mono">
                        {action.shortcut}
                      </div>
                    )}
                  </div>
                  
                  <h3 className="text-white font-semibold mb-2 group-hover:text-white/90">
                    {action.title}
                  </h3>
                  <p className="text-white/70 text-sm group-hover:text-white/80">
                    {action.description}
                  </p>

                  {/* Hover effect overlay */}
                  <div className="absolute inset-0 bg-white/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer with tips */}
        <div className="p-6 border-t border-slate-700 bg-slate-900/50">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <div className="flex items-center gap-4">
              <span>💡 Tip: Use keyboard shortcuts for faster access</span>
            </div>
            <div>
              Press <kbd className="bg-slate-800 px-2 py-1 rounded text-xs">Esc</kbd> to close
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickActionsPanel;
