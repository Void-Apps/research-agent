import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// Types for loading states
export interface LoadingState {
  isLoading: boolean;
  progress?: number;
  message?: string;
  stage?: string;
}

export interface LoadingStates {
  [key: string]: LoadingState;
}

// Hook for managing multiple loading states
export function useLoadingStates() {
  const [loadingStates, setLoadingStates] = useState<LoadingStates>({});

  const setLoading = useCallback((key: string, state: LoadingState) => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: state,
    }));
  }, []);

  const clearLoading = useCallback((key: string) => {
    setLoadingStates(prev => {
      const { [key]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  const clearAllLoading = useCallback(() => {
    setLoadingStates({});
  }, []);

  const isAnyLoading = Object.values(loadingStates).some(state => state.isLoading);
  const loadingCount = Object.values(loadingStates).filter(state => state.isLoading).length;

  return {
    loadingStates,
    setLoading,
    clearLoading,
    clearAllLoading,
    isAnyLoading,
    loadingCount,
  };
}

// Hook for research-specific loading states
export function useResearchLoadingStates() {
  const { loadingStates, setLoading, clearLoading, clearAllLoading } = useLoadingStates();

  const setSubmissionLoading = useCallback((isLoading: boolean, message?: string) => {
    if (isLoading) {
      setLoading('submission', { isLoading, message: message || 'Submitting research query...' });
    } else {
      clearLoading('submission');
    }
  }, [setLoading, clearLoading]);

  const setProcessingLoading = useCallback((isLoading: boolean, stage?: string, progress?: number) => {
    if (isLoading) {
      setLoading('processing', {
        isLoading,
        stage,
        progress,
        message: stage ? `Processing: ${stage}` : 'Processing research...',
      });
    } else {
      clearLoading('processing');
    }
  }, [setLoading, clearLoading]);

  const setResultsLoading = useCallback((isLoading: boolean, message?: string) => {
    if (isLoading) {
      setLoading('results', { isLoading, message: message || 'Loading results...' });
    } else {
      clearLoading('results');
    }
  }, [setLoading, clearLoading]);

  return {
    loadingStates,
    setSubmissionLoading,
    setProcessingLoading,
    setResultsLoading,
    clearAllLoading,
    isSubmitting: loadingStates.submission?.isLoading || false,
    isProcessing: loadingStates.processing?.isLoading || false,
    isLoadingResults: loadingStates.results?.isLoading || false,
    processingStage: loadingStates.processing?.stage,
    processingProgress: loadingStates.processing?.progress,
  };
}

// Hook for query-based loading states
export function useQueryLoadingStates(queryKeys: string[]) {
  const queryClient = useQueryClient();

  const getLoadingState = useCallback((queryKey: string) => {
    const query = queryClient.getQueryState([queryKey]);
    return {
      isLoading: query?.isFetching || false,
      isError: !!query?.error,
      error: query?.error,
      lastUpdated: query?.dataUpdatedAt,
    };
  }, [queryClient]);

  const getAllLoadingStates = useCallback(() => {
    return queryKeys.reduce((acc, key) => {
      acc[key] = getLoadingState(key);
      return acc;
    }, {} as Record<string, ReturnType<typeof getLoadingState>>);
  }, [queryKeys, getLoadingState]);

  const isAnyLoading = useCallback(() => {
    return queryKeys.some(key => getLoadingState(key).isLoading);
  }, [queryKeys, getLoadingState]);

  const hasAnyError = useCallback(() => {
    return queryKeys.some(key => getLoadingState(key).isError);
  }, [queryKeys, getLoadingState]);

  return {
    getLoadingState,
    getAllLoadingStates,
    isAnyLoading: isAnyLoading(),
    hasAnyError: hasAnyError(),
  };
}