import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache research results for 5 minutes
      staleTime: 5 * 60 * 1000,
      // Keep data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests up to 3 times with exponential backoff
      retry: (failureCount, error: any) => {
        // Don't retry on client errors (4xx)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Don't refetch on window focus for research results
      refetchOnWindowFocus: false,
      // Enable background refetching for fresh data
      refetchOnReconnect: true,
      // Refetch stale data in the background
      refetchIntervalInBackground: false,
    },
    mutations: {
      // Retry failed mutations once with delay
      retry: (failureCount, error: any) => {
        // Don't retry on client errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
      retryDelay: 1000,
    },
  },
});