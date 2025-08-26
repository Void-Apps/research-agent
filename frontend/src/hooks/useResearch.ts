import { useMutation, useQuery, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { ResearchAPI } from '@/lib/research-api';
import { SubmitResearchRequest, ResearchQuery, ResearchResult } from '@/lib/types';
import { showToast } from '@/components/ui/Toast';
import { useCallback } from 'react';

// Query keys for consistent caching
export const researchKeys = {
  all: ['research'] as const,
  results: (queryId: string) => [...researchKeys.all, 'results', queryId] as const,
  status: (queryId: string) => [...researchKeys.all, 'status', queryId] as const,
  history: () => [...researchKeys.all, 'history'] as const,
  health: () => [...researchKeys.all, 'health'] as const,
};

// Hook for submitting research queries with optimistic updates
export function useSubmitResearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SubmitResearchRequest) => ResearchAPI.submitQuery(request),
    onMutate: async (request) => {
      // Cancel any outgoing refetches for history
      await queryClient.cancelQueries({ queryKey: researchKeys.history() });

      // Snapshot the previous value
      const previousHistory = queryClient.getQueryData<ResearchQuery[]>(researchKeys.history());

      // Optimistically update history with pending query
      const optimisticQuery: ResearchQuery = {
        id: `temp-${Date.now()}`,
        query: request.query,
        user_id: request.user_id,
        timestamp: new Date().toISOString(),
        status: 'pending',
      };

      queryClient.setQueryData<ResearchQuery[]>(researchKeys.history(), (old) => 
        old ? [optimisticQuery, ...old] : [optimisticQuery]
      );

      // Return context with snapshot
      return { previousHistory, optimisticQuery };
    },
    onSuccess: (data, variables, context) => {
      // Update the optimistic entry with real data
      queryClient.setQueryData<ResearchQuery[]>(researchKeys.history(), (old) => 
        old ? old.map(query => 
          query.id === context?.optimisticQuery.id ? data : query
        ) : [data]
      );

      // Start polling for results
      queryClient.invalidateQueries({ queryKey: researchKeys.results(data.id) });
      queryClient.invalidateQueries({ queryKey: researchKeys.status(data.id) });

      showToast('Research query submitted successfully!', 'success');
    },
    onError: (error, variables, context) => {
      // Rollback optimistic update
      if (context?.previousHistory) {
        queryClient.setQueryData(researchKeys.history(), context.previousHistory);
      }

      console.error('Research submission failed:', error);
      showToast('Failed to submit research query. Please try again.', 'error');
    },
    onSettled: () => {
      // Always refetch history to ensure consistency
      queryClient.invalidateQueries({ queryKey: researchKeys.history() });
    },
  });
}

// Hook for getting research results with intelligent polling
export function useResearchResults(queryId: string, enabled: boolean = true) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: researchKeys.results(queryId),
    queryFn: () => ResearchAPI.getResults(queryId),
    enabled: enabled && !!queryId,
    // Intelligent polling based on status
    refetchInterval: (query) => {
      const data = query.state.data;
      const status = queryClient.getQueryData<{ status: string }>(researchKeys.status(queryId));
      
      // Don't poll if we have complete results
      if (data?.sources && Object.keys(data.sources).length > 0) {
        return false;
      }
      
      // Poll based on status
      if (status?.status === 'completed' || status?.status === 'failed') {
        return false;
      }
      
      // Poll every 3 seconds for pending/processing
      return status?.status === 'processing' ? 3000 : 5000;
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 404 (query not found) or 403 (forbidden)
      if (error?.response?.status === 404 || error?.response?.status === 403) {
        return false;
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Enable background refetching for fresh data
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  });
}

// Hook for getting research status with optimized polling
export function useResearchStatus(queryId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: researchKeys.status(queryId),
    queryFn: () => ResearchAPI.getStatus(queryId),
    enabled: enabled && !!queryId,
    // Optimized polling for status updates
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      
      // Stop polling when completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        return false;
      }
      
      // Poll more frequently for processing status
      return data.status === 'processing' ? 1500 : 3000;
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 404 or 403
      if (error?.response?.status === 404 || error?.response?.status === 403) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: 1000,
    // Enable background updates
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  });
}

// Hook for getting research history with caching
export function useResearchHistory() {
  return useQuery({
    queryKey: researchKeys.history(),
    queryFn: () => ResearchAPI.getHistory(),
    retry: (failureCount, error: any) => {
      // Don't retry on authentication errors
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: 1000,
    // Cache history for longer since it doesn't change frequently
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true, // Refetch when user returns to tab
  });
}

// Hook for health check with background refetching
export function useHealthCheck() {
  return useQuery({
    queryKey: researchKeys.health(),
    queryFn: () => ResearchAPI.healthCheck(),
    retry: 2,
    retryDelay: 2000,
    // Check health every 30 seconds in background
    refetchInterval: 30000,
    refetchIntervalInBackground: true,
    // Don't show loading state for health checks
    notifyOnChangeProps: ['data', 'error'],
  });
}

// Custom hook for managing research workflow
export function useResearchWorkflow(queryId?: string) {
  const queryClient = useQueryClient();
  
  const submitMutation = useSubmitResearch();
  const statusQuery = useResearchStatus(queryId || '', !!queryId);
  const resultsQuery = useResearchResults(queryId || '', !!queryId);
  
  const invalidateAll = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: researchKeys.all });
  }, [queryClient]);
  
  const clearCache = useCallback(() => {
    queryClient.removeQueries({ queryKey: researchKeys.all });
  }, [queryClient]);
  
  const prefetchResults = useCallback((queryId: string) => {
    queryClient.prefetchQuery({
      queryKey: researchKeys.results(queryId),
      queryFn: () => ResearchAPI.getResults(queryId),
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);
  
  return {
    // Mutations
    submitResearch: submitMutation.mutate,
    isSubmitting: submitMutation.isPending,
    submitError: submitMutation.error,
    
    // Queries
    status: statusQuery.data,
    isStatusLoading: statusQuery.isLoading,
    statusError: statusQuery.error,
    
    results: resultsQuery.data,
    isResultsLoading: resultsQuery.isLoading,
    resultsError: resultsQuery.error,
    
    // Utilities
    invalidateAll,
    clearCache,
    prefetchResults,
    
    // Combined states
    isLoading: submitMutation.isPending || statusQuery.isLoading || resultsQuery.isLoading,
    hasError: !!(submitMutation.error || statusQuery.error || resultsQuery.error),
    isComplete: statusQuery.data?.status === 'completed' && !!resultsQuery.data,
  };
}