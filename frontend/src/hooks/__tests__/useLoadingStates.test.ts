import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import React from 'react';
import { useLoadingStates, useResearchLoadingStates, useQueryLoadingStates } from '../useLoadingStates';

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

describe('useLoadingStates hooks', () => {
  describe('useLoadingStates', () => {
    it('should manage multiple loading states', () => {
      const { result } = renderHook(() => useLoadingStates());

      expect(result.current.loadingStates).toEqual({});
      expect(result.current.isAnyLoading).toBe(false);
      expect(result.current.loadingCount).toBe(0);

      // Set loading state
      act(() => {
        result.current.setLoading('test', { isLoading: true, message: 'Testing...' });
      });

      expect(result.current.loadingStates.test).toEqual({
        isLoading: true,
        message: 'Testing...',
      });
      expect(result.current.isAnyLoading).toBe(true);
      expect(result.current.loadingCount).toBe(1);

      // Clear loading state
      act(() => {
        result.current.clearLoading('test');
      });

      expect(result.current.loadingStates.test).toBeUndefined();
      expect(result.current.isAnyLoading).toBe(false);
      expect(result.current.loadingCount).toBe(0);
    });

    it('should clear all loading states', () => {
      const { result } = renderHook(() => useLoadingStates());

      // Set multiple loading states
      act(() => {
        result.current.setLoading('test1', { isLoading: true });
        result.current.setLoading('test2', { isLoading: true });
      });

      expect(result.current.loadingCount).toBe(2);

      // Clear all
      act(() => {
        result.current.clearAllLoading();
      });

      expect(result.current.loadingStates).toEqual({});
      expect(result.current.loadingCount).toBe(0);
    });
  });

  describe('useResearchLoadingStates', () => {
    it('should manage research-specific loading states', () => {
      const { result } = renderHook(() => useResearchLoadingStates());

      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.isProcessing).toBe(false);
      expect(result.current.isLoadingResults).toBe(false);

      // Set submission loading
      act(() => {
        result.current.setSubmissionLoading(true, 'Submitting query...');
      });

      expect(result.current.isSubmitting).toBe(true);
      expect(result.current.loadingStates.submission?.message).toBe('Submitting query...');

      // Set processing loading
      act(() => {
        result.current.setProcessingLoading(true, 'Analyzing data', 50);
      });

      expect(result.current.isProcessing).toBe(true);
      expect(result.current.processingStage).toBe('Analyzing data');
      expect(result.current.processingProgress).toBe(50);

      // Set results loading
      act(() => {
        result.current.setResultsLoading(true);
      });

      expect(result.current.isLoadingResults).toBe(true);

      // Clear all
      act(() => {
        result.current.clearAllLoading();
      });

      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.isProcessing).toBe(false);
      expect(result.current.isLoadingResults).toBe(false);
    });

    it('should use default messages when not provided', () => {
      const { result } = renderHook(() => useResearchLoadingStates());

      act(() => {
        result.current.setSubmissionLoading(true);
        result.current.setProcessingLoading(true);
        result.current.setResultsLoading(true);
      });

      expect(result.current.loadingStates.submission?.message).toBe('Submitting research query...');
      expect(result.current.loadingStates.processing?.message).toBe('Processing research...');
      expect(result.current.loadingStates.results?.message).toBe('Loading results...');
    });
  });

  describe('useQueryLoadingStates', () => {
    it('should track query loading states', () => {
      const queryKeys = ['query1', 'query2'];
      const { result } = renderHook(() => useQueryLoadingStates(queryKeys), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.getLoadingState).toBe('function');
      expect(typeof result.current.getAllLoadingStates).toBe('function');
      expect(result.current.isAnyLoading).toBe(false);
      expect(result.current.hasAnyError).toBe(false);

      // Test getting loading state for a specific query
      const loadingState = result.current.getLoadingState('query1');
      expect(loadingState).toHaveProperty('isLoading');
      expect(loadingState).toHaveProperty('isError');
      expect(loadingState).toHaveProperty('error');
      expect(loadingState).toHaveProperty('lastUpdated');

      // Test getting all loading states
      const allStates = result.current.getAllLoadingStates();
      expect(allStates).toHaveProperty('query1');
      expect(allStates).toHaveProperty('query2');
    });
  });
});