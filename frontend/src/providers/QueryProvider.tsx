'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/query-client';
import { ReactNode, useEffect } from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { showToast } from '@/components/ui/Toast';

interface QueryProviderProps {
  children: ReactNode;
}

export default function QueryProvider({ children }: QueryProviderProps) {
  useEffect(() => {
    // Global error handler for React Query
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'queryUpdated' && event.query.state.error) {
        const error = event.query.state.error as any;
        
        // Don't show toast for certain error types
        if (error?.response?.status === 404 || error?.response?.status === 401) {
          return;
        }

        // Show toast for unexpected errors
        if (error?.response?.status >= 500) {
          showToast('Server error occurred. Please try again later.', 'error');
        } else if (!navigator.onLine) {
          showToast('You appear to be offline. Please check your connection.', 'error');
        }
      }
    });

    return unsubscribe;
  }, []);

  return (
    <ErrorBoundary
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Something went wrong with the application
            </h2>
            <p className="text-gray-600 mb-4">
              Please refresh the page to try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      }
    >
      <QueryClientProvider client={queryClient}>
        {children}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}