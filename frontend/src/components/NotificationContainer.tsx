import React from 'react';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { type Notification } from '../hooks/useNotifications';
import '../styles/modern-dark-theme.css';

interface NotificationToastProps {
  notification: Notification;
  onRemove: (id: string) => void;
}

const NotificationToast: React.FC<NotificationToastProps> = ({ notification, onRemove }) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-400" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400" />;
      case 'info':
        return <InformationCircleIcon className="w-5 h-5 text-blue-400" />;
      default:
        return <InformationCircleIcon className="w-5 h-5 text-slate-400" />;
    }
  };

  const getBorderColor = () => {
    switch (notification.type) {
      case 'success':
        return 'border-green-500/50';
      case 'error':
        return 'border-red-500/50';
      case 'warning':
        return 'border-yellow-500/50';
      case 'info':
        return 'border-blue-500/50';
      default:
        return 'border-slate-500/50';
    }
  };

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-900/20';
      case 'error':
        return 'bg-red-900/20';
      case 'warning':
        return 'bg-yellow-900/20';
      case 'info':
        return 'bg-blue-900/20';
      default:
        return 'bg-slate-900/20';
    }
  };

  return (
    <div className={`toast ${getBorderColor()} ${getBackgroundColor()} backdrop-blur-xl`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-slate-200 mb-1">
            {notification.title}
          </h4>
          <p className="text-sm text-slate-300">
            {notification.message}
          </p>
        </div>
        <button
          onClick={() => onRemove(notification.id)}
          className="flex-shrink-0 text-slate-400 hover:text-slate-200 transition-colors p-1 hover:bg-slate-700/50 rounded"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

interface NotificationContainerProps {
  notifications: Notification[];
  onRemove: (id: string) => void;
}

const NotificationContainer: React.FC<NotificationContainerProps> = ({ notifications, onRemove }) => {
  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
};

export default NotificationContainer;
