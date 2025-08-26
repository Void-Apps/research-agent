'use client';

import { useCallback } from 'react';
import { showToast } from '@/components/ui/Toast';
import { useOnlineStatus } from './useOnlineStatus';

interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

interface ErrorHandlerOptions {
  showToast?: boolean;
  fallbackMessage?: string;
  onError?: (error: ApiError) => void;
}

export function useErrorHandler() {
  const { isOnline } = useOnlineStatus();

  const handleError = useCallback((
    error: any,
    options: ErrorHandlerOptions = {}
  ): ApiError => {
    const {
      showToast: shouldShowToast = true,
      fallbackMessage = 'An unexpected error occurred',
      onError,
    } = options;

    let apiError: ApiError;

    // Handle different error types
    if (error?.response) {
      // HTTP error response
      const status = error.response.status;
      const data = error.response.data;
      
      apiError = {
        message: data?.message || data?.error || getStatusMessage(status),
        status,
        code: data?.code,
      };
    } else if (error?.request) {
      // Network error
      apiError = {
        message: isOnline 
          ? 'Unable to connect to the server. Please try again.'
          : 'You appear to be offline. Please check your connection.',
        status: 0,
        code: 'NETWORK_ERROR',
      };
    } else if (error?.message) {
      // JavaScript error
      apiError = {
        message: error.message,
        code: 'CLIENT_ERROR',
      };
    } else {
      // Unknown error
      apiError = {
        message: fallbackMessage,
        code: 'UNKNOWN_ERROR',
      };
    }

    // Show toast notification if requested
    if (shouldShowToast) {
      showToast.error(apiError.message);
    }

    // Call custom error handler if provided
    if (onError) {
      onError(apiError);
    }

    // Log error for debugging
    console.error('Error handled:', { originalError: error, apiError });

    return apiError;
  }, [isOnline]);

  const handleAsyncError = useCallback(async <T>(
    asyncFn: () => Promise<T>,
    options: ErrorHandlerOptions = {}
  ): Promise<T | null> => {
    try {
      return await asyncFn();
    } catch (error) {
      handleError(error, options);
      return null;
    }
  }, [handleError]);

  return {
    handleError,
    handleAsyncError,
  };
}

// Helper function to get user-friendly status messages
function getStatusMessage(status: number): string {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input and try again.';
    case 401:
      return 'Authentication required. Please log in and try again.';
    case 403:
      return 'You don\'t have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 408:
      return 'Request timeout. Please try again.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
      return 'Server error. Please try again later.';
    case 502:
      return 'Service temporarily unavailable. Please try again later.';
    case 503:
      return 'Service unavailable. Please try again later.';
    case 504:
      return 'Request timeout. Please try again.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
}