import { Link } from 'react-router-dom';
import { 
  ChatBubbleBottomCenterTextIcon, 
  DocumentTextIcon, 
  CloudArrowUpIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline';

const HomePage: React.FC = () => {
  const features = [
    {
      name: 'AI-Powered Chat',
      description: 'Ask questions about your documents and get intelligent responses powered by RAG technology.',
      icon: ChatBubbleBottomCenterTextIcon,
      href: '/chat',
      color: 'bg-blue-500',
    },
    {
      name: 'Document Management',
      description: 'Upload, organize, and manage your document collection with ease.',
      icon: DocumentTextIcon,
      href: '/documents',
      color: 'bg-green-500',
    },
    {
      name: 'Smart Upload',
      description: 'Drag and drop files to automatically process and vectorize your documents.',
      icon: CloudArrowUpIcon,
      href: '/documents',
      color: 'bg-purple-500',
    },
    {
      name: 'Advanced RAG',
      description: 'Leverage retrieval-augmented generation for accurate, context-aware answers.',
      icon: SparklesIcon,
      href: '/chat',
      color: 'bg-orange-500',
    },
  ];

  const stats = [
    { name: 'Documents Processed', value: '0', unit: '' },
    { name: 'Questions Answered', value: '0', unit: '' },
    { name: 'Storage Used', value: '0', unit: 'MB' },
    { name: 'Response Time', value: '<1', unit: 's' },
  ];

  return (
    <div className="min-h-full">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-primary-600 to-primary-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              Welcome to <span className="text-primary-200">AskRAG</span>
            </h1>
            <p className="mt-6 text-xl text-primary-100 max-w-3xl mx-auto">
              Your intelligent document assistant powered by Retrieval-Augmented Generation. 
              Upload documents, ask questions, and get precise answers backed by your content.
            </p>
            <div className="mt-10 flex items-center justify-center gap-6">
              <Link
                to="/chat"
                className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors duration-200"
              >
                Start Chatting
              </Link>
              <Link
                to="/documents"
                className="border border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-600 transition-colors duration-200"
              >
                Upload Documents
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.name} className="bg-gray-50 overflow-hidden rounded-lg p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                <dd className="mt-1 text-3xl font-semibold text-gray-900">
                  {stat.value}{stat.unit}
                </dd>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">
              Powerful Features
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Everything you need to interact with your documents intelligently
            </p>
          </div>

          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <Link
                key={feature.name}
                to={feature.href}
                className="group relative bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
              >
                <div>
                  <span className={`inline-flex p-3 rounded-lg ${feature.color}`}>
                    <feature.icon className="w-6 h-6 text-white" aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900 group-hover:text-primary-600">
                    {feature.name}
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    {feature.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Getting Started Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-primary-600 rounded-2xl px-6 py-16 sm:p-16">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-white">
                Ready to get started?
              </h2>
              <p className="mt-4 text-lg text-primary-100">
                Upload your first document and start asking questions in minutes.
              </p>
              <div className="mt-8">
                <Link
                  to="/documents"
                  className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors duration-200"
                >
                  Upload Your First Document
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
