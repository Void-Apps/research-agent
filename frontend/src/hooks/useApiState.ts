import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';
import { useOnlineStatus } from './useOnlineStatus';

// Hook for managing API connection state
export function useApiConnection() {
  const isOnline = useOnlineStatus();
  const [isConnected, setIsConnected] = useState(true);
  const [lastConnected, setLastConnected] = useState<Date | null>(null);

  // Simple connectivity check
  const checkConnection = useCallback(async () => {
    if (!isOnline) {
      setIsConnected(false);
      return false;
    }

    try {
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache',
      });
      const connected = response.ok;
      setIsConnected(connected);
      if (connected) {
        setLastConnected(new Date());
      }
      return connected;
    } catch {
      setIsConnected(false);
      return false;
    }
  }, [isOnline]);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkConnection]);

  return {
    isOnline,
    isConnected,
    lastConnected,
    checkConnection,
  };
}

// Hook for managing query states across the app
export function useGlobalQueryState() {
  const queryClient = useQueryClient();
  const [isFetching, setIsFetching] = useState(false);
  const [hasErrors, setHasErrors] = useState(false);

  useEffect(() => {
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'queryUpdated') {
        const queries = queryClient.getQueryCache().getAll();
        const fetchingQueries = queries.filter(query => query.state.isFetching);
        const errorQueries = queries.filter(query => query.state.error);
        
        setIsFetching(fetchingQueries.length > 0);
        setHasErrors(errorQueries.length > 0);
      }
    });

    return unsubscribe;
  }, [queryClient]);

  const retryFailedQueries = useCallback(() => {
    const queries = queryClient.getQueryCache().getAll();
    const failedQueries = queries.filter(query => query.state.error);
    
    failedQueries.forEach(query => {
      queryClient.invalidateQueries({ queryKey: query.queryKey });
    });
  }, [queryClient]);

  const clearAllErrors = useCallback(() => {
    const queries = queryClient.getQueryCache().getAll();
    queries.forEach(query => {
      if (query.state.error) {
        queryClient.resetQueries({ queryKey: query.queryKey });
      }
    });
  }, [queryClient]);

  return {
    isFetching,
    hasErrors,
    retryFailedQueries,
    clearAllErrors,
  };
}

// Hook for optimistic UI updates
export function useOptimisticUpdates<T>(
  queryKey: unknown[],
  updateFn: (oldData: T | undefined, newData: Partial<T>) => T
) {
  const queryClient = useQueryClient();

  const optimisticUpdate = useCallback(
    async (newData: Partial<T>) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<T>(queryKey);

      // Optimistically update
      queryClient.setQueryData<T>(queryKey, (old) => updateFn(old, newData));

      // Return rollback function
      return () => {
        queryClient.setQueryData(queryKey, previousData);
      };
    },
    [queryClient, queryKey, updateFn]
  );

  return { optimisticUpdate };
}

// Hook for background sync
export function useBackgroundSync() {
  const queryClient = useQueryClient();
  const { isConnected } = useApiConnection();

  const syncAll = useCallback(() => {
    if (!isConnected) return;

    // Refetch all stale queries
    queryClient.refetchQueries({
      type: 'active',
      stale: true,
    });
  }, [queryClient, isConnected]);

  useEffect(() => {
    if (isConnected) {
      // Sync when connection is restored
      syncAll();
    }
  }, [isConnected, syncAll]);

  return { syncAll };
}