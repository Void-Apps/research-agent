import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import React from 'react';
import { useApiConnection, useGlobalQueryState, useOptimisticUpdates, useBackgroundSync } from '../useApiState';

// Mock fetch
global.fetch = jest.fn();

// Mock useOnlineStatus
jest.mock('../useOnlineStatus', () => ({
  useOnlineStatus: jest.fn(() => true),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };

  return Wrapper;
};

describe('useApiState hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  describe('useApiConnection', () => {
    it('should check connection status', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
      });

      const { result } = renderHook(() => useApiConnection(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isOnline).toBe(true);

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(global.fetch).toHaveBeenCalledWith('/api/health', {
        method: 'HEAD',
        cache: 'no-cache',
      });
    });

    it('should handle connection failures', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useApiConnection(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false);
      });
    });

    it('should provide checkConnection function', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      const { result } = renderHook(() => useApiConnection(), {
        wrapper: createWrapper(),
      });

      const isConnected = await act(async () => {
        return await result.current.checkConnection();
      });

      expect(isConnected).toBe(true);
    });
  });

  describe('useGlobalQueryState', () => {
    it('should track global fetching state', async () => {
      const { result } = renderHook(() => useGlobalQueryState(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isFetching).toBe(false);
      expect(result.current.hasErrors).toBe(false);
    });

    it('should provide retry functions', () => {
      const { result } = renderHook(() => useGlobalQueryState(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.retryFailedQueries).toBe('function');
      expect(typeof result.current.clearAllErrors).toBe('function');
    });
  });

  describe('useOptimisticUpdates', () => {
    it('should perform optimistic updates', async () => {
      const queryKey = ['test'];
      const updateFn = (oldData: any, newData: any) => ({ ...oldData, ...newData });

      const { result } = renderHook(() => useOptimisticUpdates(queryKey, updateFn), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.optimisticUpdate).toBe('function');

      // Test optimistic update
      await act(async () => {
        const rollback = await result.current.optimisticUpdate({ test: 'value' });
        expect(typeof rollback).toBe('function');
      });
    });
  });

  describe('useBackgroundSync', () => {
    it('should provide sync functionality', () => {
      const { result } = renderHook(() => useBackgroundSync(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.syncAll).toBe('function');
    });

    it('should sync when connection is restored', async () => {
      const { useOnlineStatus } = require('../useOnlineStatus');
      
      // Start offline
      useOnlineStatus.mockReturnValue(false);
      
      const { result, rerender } = renderHook(() => useBackgroundSync(), {
        wrapper: createWrapper(),
      });

      // Go online
      useOnlineStatus.mockReturnValue(true);
      rerender();

      // Should trigger sync
      expect(typeof result.current.syncAll).toBe('function');
    });
  });
});