'use client';

import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void | Promise<void>;
  retryText?: string;
  showRetry?: boolean;
  variant?: 'inline' | 'card' | 'banner';
  className?: string;
}

export default function ErrorMessage({
  title = 'Something went wrong',
  message,
  onRetry,
  retryText = 'Try again',
  showRetry = true,
  variant = 'card',
  className = '',
}: ErrorMessageProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    if (!onRetry) return;
    
    setIsRetrying(true);
    try {
      await onRetry();
    } catch (error) {
      console.error('Retry failed:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  const baseClasses = 'flex items-start space-x-3';
  
  const variantClasses = {
    inline: 'p-3 bg-red-50 border border-red-200 rounded-md',
    card: 'p-6 bg-white border border-red-200 rounded-lg shadow-sm',
    banner: 'p-4 bg-red-50 border-l-4 border-red-400',
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      <div className="flex-shrink-0">
        <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
      </div>
      
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-red-800">
          {title}
        </h3>
        <div className="mt-1 text-sm text-red-700">
          <p>{message}</p>
        </div>
        
        {showRetry && onRetry && (
          <div className="mt-3">
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="inline-flex items-center space-x-2 text-sm font-medium text-red-600 hover:text-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowPathIcon 
                className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} 
              />
              <span>{isRetrying ? 'Retrying...' : retryText}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}