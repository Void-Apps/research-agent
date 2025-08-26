import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import React from 'react';
import { useSubmitResearch, useResearchResults, useResearchStatus, useResearchHistory, useResearchWorkflow } from '../useResearch';
import { ResearchAPI } from '@/lib/research-api';

// Mock the ResearchAPI
jest.mock('@/lib/research-api');
const mockResearchAPI = ResearchAPI as jest.Mocked<typeof ResearchAPI>;

// Mock toast
jest.mock('@/components/ui/Toast', () => ({
  showToast: jest.fn(),
}));

// Test wrapper with QueryClient
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

describe('useResearch hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useSubmitResearch', () => {
    it('should submit research query successfully', async () => {
      const mockQuery = {
        id: 'test-id',
        query: 'test query',
        timestamp: '2024-01-01T00:00:00Z',
        status: 'pending' as const,
      };

      mockResearchAPI.submitQuery.mockResolvedValue(mockQuery);

      const { result } = renderHook(() => useSubmitResearch(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ query: 'test query' });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockResearchAPI.submitQuery).toHaveBeenCalledWith({ query: 'test query' });
      expect(result.current.data).toEqual(mockQuery);
    });

    it('should handle submission errors', async () => {
      const error = new Error('Submission failed');
      mockResearchAPI.submitQuery.mockRejectedValue(error);

      const { result } = renderHook(() => useSubmitResearch(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ query: 'test query' });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should perform optimistic updates', async () => {
      const mockQuery = {
        id: 'test-id',
        query: 'test query',
        timestamp: '2024-01-01T00:00:00Z',
        status: 'pending' as const,
      };

      mockResearchAPI.submitQuery.mockResolvedValue(mockQuery);

      const { result } = renderHook(() => useSubmitResearch(), {
        wrapper: createWrapper(),
      });

      // The optimistic update should happen immediately
      result.current.mutate({ query: 'test query' });

      expect(result.current.isPending).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });
    });
  });

  describe('useResearchResults', () => {
    it('should fetch research results', async () => {
      const mockResults = {
        query_id: 'test-id',
        sources: {
          google_scholar: [
            {
              title: 'Test Paper',
              authors: ['Author 1'],
              source_type: 'google_scholar' as const,
            },
          ],
        },
        summary: 'Test summary',
        confidence_score: 0.8,
        cached: false,
      };

      mockResearchAPI.getResults.mockResolvedValue(mockResults);

      const { result } = renderHook(() => useResearchResults('test-id'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockResearchAPI.getResults).toHaveBeenCalledWith('test-id');
      expect(result.current.data).toEqual(mockResults);
    });

    it('should not fetch when disabled', () => {
      const { result } = renderHook(() => useResearchResults('test-id', false), {
        wrapper: createWrapper(),
      });

      expect(result.current.isFetching).toBe(false);
      expect(mockResearchAPI.getResults).not.toHaveBeenCalled();
    });

    it('should handle 404 errors gracefully', async () => {
      const error = { response: { status: 404 } };
      mockResearchAPI.getResults.mockRejectedValue(error);

      const { result } = renderHook(() => useResearchResults('test-id'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('useResearchStatus', () => {
    it('should fetch research status', async () => {
      const mockStatus = { status: 'processing', progress: 50 };
      mockResearchAPI.getStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useResearchStatus('test-id'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockResearchAPI.getStatus).toHaveBeenCalledWith('test-id');
      expect(result.current.data).toEqual(mockStatus);
    });

    it('should stop polling when completed', async () => {
      const mockStatus = { status: 'completed' };
      mockResearchAPI.getStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useResearchStatus('test-id'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // The refetchInterval should return false for completed status
      expect(result.current.data?.status).toBe('completed');
    });
  });

  describe('useResearchHistory', () => {
    it('should fetch research history', async () => {
      const mockHistory = [
        {
          id: 'test-1',
          query: 'query 1',
          timestamp: '2024-01-01T00:00:00Z',
          status: 'completed' as const,
        },
        {
          id: 'test-2',
          query: 'query 2',
          timestamp: '2024-01-02T00:00:00Z',
          status: 'pending' as const,
        },
      ];

      mockResearchAPI.getHistory.mockResolvedValue(mockHistory);

      const { result } = renderHook(() => useResearchHistory(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockResearchAPI.getHistory).toHaveBeenCalled();
      expect(result.current.data).toEqual(mockHistory);
    });

    it('should handle authentication errors', async () => {
      const error = { response: { status: 401 } };
      mockResearchAPI.getHistory.mockRejectedValue(error);

      const { result } = renderHook(() => useResearchHistory(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('useResearchWorkflow', () => {
    it('should manage complete research workflow', async () => {
      const mockQuery = {
        id: 'test-id',
        query: 'test query',
        timestamp: '2024-01-01T00:00:00Z',
        status: 'pending' as const,
      };

      const mockStatus = { status: 'processing', progress: 50 };
      const mockResults = {
        query_id: 'test-id',
        sources: {},
        summary: 'Test summary',
        confidence_score: 0.8,
        cached: false,
      };

      mockResearchAPI.submitQuery.mockResolvedValue(mockQuery);
      mockResearchAPI.getStatus.mockResolvedValue(mockStatus);
      mockResearchAPI.getResults.mockResolvedValue(mockResults);

      const { result } = renderHook(() => useResearchWorkflow('test-id'), {
        wrapper: createWrapper(),
      });

      // Initially should not be loading
      expect(result.current.isLoading).toBe(true); // Status and results queries are loading

      await waitFor(() => {
        expect(result.current.status).toEqual(mockStatus);
        expect(result.current.results).toEqual(mockResults);
      });

      expect(result.current.isComplete).toBe(false); // Status is processing, not completed
    });

    it('should provide utility functions', () => {
      const { result } = renderHook(() => useResearchWorkflow(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.invalidateAll).toBe('function');
      expect(typeof result.current.clearCache).toBe('function');
      expect(typeof result.current.prefetchResults).toBe('function');
      expect(typeof result.current.submitResearch).toBe('function');
    });
  });
});