import React, { useState, useEffect, useMemo } from 'react';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  ClockIcon,
  CalendarIcon,
  FunnelIcon,
  SparklesIcon,
  DocumentIcon,
  ChatBubbleBottomCenterTextIcon
} from '@heroicons/react/24/outline';
import '../styles/modern-dark-theme.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  files?: File[];
  urls?: string[];
}

interface SearchResult {
  message: Message;
  matchScore: number;
  highlightedContent: string;
}

interface ChatSearchProps {
  isOpen: boolean;
  onClose: () => void;
  messages: Message[];
  onMessageSelect: (messageId: string) => void;
}

const ChatSearch: React.FC<ChatSearchProps> = ({ 
  isOpen, 
  onClose, 
  messages, 
  onMessageSelect 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'user' | 'assistant' | 'files'>('all');
  const [dateRange, setDateRange] = useState<'all' | 'today' | 'week' | 'month'>('all');
  const [sortBy, setSortBy] = useState<'relevance' | 'date'>('relevance');

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];

    const query = searchQuery.toLowerCase();
    const results: SearchResult[] = [];

    messages.forEach(message => {
      // Filter by type
      if (selectedFilter !== 'all') {
        if (selectedFilter === 'files' && (!message.files || message.files.length === 0)) return;
        if (selectedFilter !== 'files' && message.type !== selectedFilter) return;
      }

      // Filter by date
      if (dateRange !== 'all') {
        const now = new Date();
        const messageDate = new Date(message.timestamp);
        const daysDiff = (now.getTime() - messageDate.getTime()) / (1000 * 3600 * 24);

        if (dateRange === 'today' && daysDiff > 1) return;
        if (dateRange === 'week' && daysDiff > 7) return;
        if (dateRange === 'month' && daysDiff > 30) return;
      }

      // Search in content
      const content = message.content.toLowerCase();
      if (content.includes(query)) {
        const startIndex = content.indexOf(query);
        const matchScore = calculateMatchScore(query, content, startIndex);
        const highlightedContent = highlightText(message.content, searchQuery);
        
        results.push({
          message,
          matchScore,
          highlightedContent
        });
      }

      // Search in file names
      if (message.files) {
        message.files.forEach(file => {
          if (file.name.toLowerCase().includes(query)) {
            const matchScore = calculateMatchScore(query, file.name.toLowerCase(), 0) + 0.1; // Bonus for file match
            const highlightedContent = `📎 ${highlightText(file.name, searchQuery)}`;
            
            results.push({
              message,
              matchScore,
              highlightedContent: highlightedContent + '\n' + message.content
            });
          }
        });
      }

      // Search in URLs
      if (message.urls) {
        message.urls.forEach(url => {
          if (url.toLowerCase().includes(query)) {
            const matchScore = calculateMatchScore(query, url.toLowerCase(), 0) + 0.05; // Bonus for URL match
            const highlightedContent = `🔗 ${highlightText(url, searchQuery)}`;
            
            results.push({
              message,
              matchScore,
              highlightedContent: highlightedContent + '\n' + message.content
            });
          }
        });
      }
    });

    // Remove duplicates and sort
    const uniqueResults = Array.from(
      new Map(results.map(r => [r.message.id, r])).values()
    );

    return uniqueResults.sort((a, b) => {
      if (sortBy === 'relevance') {
        return b.matchScore - a.matchScore;
      } else {
        return new Date(b.message.timestamp).getTime() - new Date(a.message.timestamp).getTime();
      }
    });
  }, [searchQuery, messages, selectedFilter, dateRange, sortBy]);

  const calculateMatchScore = (query: string, text: string, index: number): number => {
    let score = 0.5; // Base score
    
    // Exact match bonus
    if (text === query) score += 0.5;
    
    // Start of text bonus
    if (index === 0) score += 0.2;
    
    // Word boundary bonus
    if (index === 0 || text[index - 1] === ' ') score += 0.1;
    
    // Length ratio bonus (shorter text with match = higher relevance)
    score += (1 - (text.length - query.length) / text.length) * 0.2;
    
    return Math.min(score, 1);
  };

  const highlightText = (text: string, query: string): string => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  };

  const formatDate = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-teal-500 rounded-lg flex items-center justify-center">
              <MagnifyingGlassIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-200">Search Chat History</h2>
              <p className="text-sm text-slate-400">Find messages, files, and links</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors p-2 hover:bg-slate-800/50 rounded-lg"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-6 border-b border-slate-700 space-y-4">
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search messages, files, links..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              autoFocus
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-4 flex-wrap">
            {/* Type Filter */}
            <div className="flex items-center gap-2">
              <FunnelIcon className="w-4 h-4 text-slate-400" />
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value as any)}
                className="bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-1 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Messages</option>
                <option value="user">My Messages</option>
                <option value="assistant">AI Responses</option>
                <option value="files">With Files</option>
              </select>
            </div>

            {/* Date Filter */}
            <div className="flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-slate-400" />
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value as any)}
                className="bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-1 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </select>
            </div>

            {/* Sort By */}
            <div className="flex items-center gap-2">
              <ClockIcon className="w-4 h-4 text-slate-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-1 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="relevance">Relevance</option>
                <option value="date">Date</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6 max-h-[50vh]">
          {searchQuery.trim() === '' ? (
            <div className="text-center py-12">
              <MagnifyingGlassIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">Start typing to search</h3>
              <p className="text-slate-500">Search through your conversation history</p>
            </div>
          ) : searchResults.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <MagnifyingGlassIcon className="w-8 h-8 text-slate-500" />
              </div>
              <h3 className="text-lg font-medium text-slate-400 mb-2">No results found</h3>
              <p className="text-slate-500">Try adjusting your search terms or filters</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-sm text-slate-400 mb-4">
                Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
              </div>
              {searchResults.map((result, index) => (
                <div
                  key={`${result.message.id}-${index}`}
                  className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 hover:bg-slate-800/50 transition-colors cursor-pointer"
                  onClick={() => {
                    onMessageSelect(result.message.id);
                    onClose();
                  }}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      result.message.type === 'user'
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500'
                        : 'bg-gradient-to-r from-teal-500 to-emerald-500'
                    }`}>
                      {result.message.type === 'user' ? (
                        <ChatBubbleBottomCenterTextIcon className="w-4 h-4 text-white" />
                      ) : (
                        <SparklesIcon className="w-4 h-4 text-white" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium text-slate-300">
                          {result.message.type === 'user' ? 'You' : 'AI Assistant'}
                        </span>
                        <span className="text-xs text-slate-500">
                          {formatDate(result.message.timestamp)}
                        </span>
                        {result.message.files && result.message.files.length > 0 && (
                          <DocumentIcon className="w-4 h-4 text-purple-400" />
                        )}
                      </div>

                      <div 
                        className="text-sm text-slate-200 line-clamp-3"
                        dangerouslySetInnerHTML={{ 
                          __html: result.highlightedContent.replace(/\n/g, '<br/>') 
                        }}
                      />

                      {result.matchScore > 0.8 && (
                        <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1">
                          <SparklesIcon className="w-3 h-3" />
                          High relevance match
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Custom styles for search highlighting */}
      <style jsx>{`
        mark {
          background-color: rgba(168, 85, 247, 0.3);
          color: rgb(196, 181, 253);
          padding: 1px 2px;
          border-radius: 2px;
        }
        
        .line-clamp-3 {
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};

export default ChatSearch;
