import React, { useState, useEffect } from 'react';
import { 
  DocumentTextIcon, 
  ChatBubbleLeftRightIcon, 
  ClockIcon, 
  ChartBarIcon,
  PlusIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import DocumentUpload from './DocumentUpload';
import ChatRAG from './ChatRAG';
import { useToast } from '../contexts/ToastContext';

const AskRAGDashboard = ({ sessionId }) => {
  const [stats, setStats] = useState({
    totalDocuments: 0,
    totalChats: 0,
    avgResponseTime: 0,
    recentActivity: []
  });
  const { showToast } = useToast();

  useEffect(() => {
    // Simulate loading stats
    setTimeout(() => {
      setStats({
        totalDocuments: 12,
        totalChats: 45,
        avgResponseTime: 1.2,
        recentActivity: [
          { type: 'upload', document: 'Research Paper.pdf', time: '2 minutes ago' },
          { type: 'chat', question: 'What is machine learning?', time: '5 minutes ago' },
          { type: 'upload', document: 'Technical Manual.docx', time: '1 hour ago' },
        ]
      });
    }, 1000);
  }, []);

  const handleUploadSuccess = (fileName) => {
    showToast('success', 'Document uploaded successfully', `${fileName} has been processed and is ready for questions.`);
    setStats(prev => ({
      ...prev,
      totalDocuments: prev.totalDocuments + 1,
      recentActivity: [
        { type: 'upload', document: fileName, time: 'just now' },
        ...prev.recentActivity.slice(0, 4)
      ]
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Welcome to AskRAG</h1>
        <p className="mt-2 text-gray-600">
          Upload documents and chat with your knowledge base using AI-powered search.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <DocumentTextIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">{stats.totalDocuments}</h3>
              <p className="text-gray-500">Documents Uploaded</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">{stats.totalChats}</h3>
              <p className="text-gray-500">Conversations</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <ClockIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">{stats.avgResponseTime}s</h3>
              <p className="text-gray-500">Avg Response Time</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Document Upload Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Upload Documents</h2>
            <Link 
              to="/documents" 
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              View All
            </Link>
          </div>
          <DocumentUpload onUpload={handleUploadSuccess} />
        </div>

        {/* Chat Section */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">AI Assistant</h2>
            <Link 
              to="/chat" 
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Full Chat
            </Link>
          </div>
          <div className="h-96">
            <ChatRAG sessionId={sessionId} />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Activity</h2>
          <ChartBarIcon className="h-6 w-6 text-gray-400" />
        </div>
        <div className="space-y-4">
          {stats.recentActivity.map((activity, index) => (
            <div key={index} className="flex items-center space-x-3 py-2">
              <div className={`p-2 rounded-lg ${
                activity.type === 'upload' 
                  ? 'bg-blue-100 text-blue-600' 
                  : 'bg-green-100 text-green-600'
              }`}>
                {activity.type === 'upload' 
                  ? <DocumentTextIcon className="h-4 w-4" />
                  : <ChatBubbleLeftRightIcon className="h-4 w-4" />
                }
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">
                  {activity.type === 'upload' 
                    ? `Uploaded ${activity.document}` 
                    : `Asked: "${activity.question}"`
                  }
                </p>
                <p className="text-xs text-gray-500">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link 
          to="/documents" 
          className="bg-blue-50 border border-blue-200 rounded-lg p-4 hover:bg-blue-100 transition-colors"
        >
          <div className="flex items-center">
            <PlusIcon className="h-6 w-6 text-blue-600 mr-3" />
            <div>
              <h3 className="font-medium text-blue-900">Upload New Document</h3>
              <p className="text-sm text-blue-600">Add documents to your knowledge base</p>
            </div>
          </div>
        </Link>

        <Link 
          to="/chat" 
          className="bg-green-50 border border-green-200 rounded-lg p-4 hover:bg-green-100 transition-colors"
        >
          <div className="flex items-center">
            <ChatBubbleLeftRightIcon className="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h3 className="font-medium text-green-900">Start New Chat</h3>
              <p className="text-sm text-green-600">Ask questions about your documents</p>
            </div>
          </div>
        </Link>

        <Link 
          to="/settings" 
          className="bg-purple-50 border border-purple-200 rounded-lg p-4 hover:bg-purple-100 transition-colors"
        >
          <div className="flex items-center">
            <ArrowTrendingUpIcon className="h-6 w-6 text-purple-600 mr-3" />
            <div>
              <h3 className="font-medium text-purple-900">View Analytics</h3>
              <p className="text-sm text-purple-600">Check your usage statistics</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
};

export default AskRAGDashboard;
