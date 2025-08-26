/**
 * Integration tests for API state management
 */
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useResearch } from '../../hooks/useResearch'
import { useApiState } from '../../hooks/useApiState'
import { mockApiResponses, createMockFetch, createMockFetchError } from '../fixtures/mockData'

// Create wrapper for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('API State Management Integration', () => {
  beforeEach(() => {
    // Reset fetch mock
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('useResearch hook integration', () => {
    it('should handle successful research flow', async () => {
      const mockFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // Initial state
      expect(result.current.isLoading).toBe(false)
      expect(result.current.data).toBeNull()
      expect(result.current.error).toBeNull()

      // Start research
      result.current.submitResearch('artificial intelligence')

      // Should be loading
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true)
      })

      // Should complete successfully
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.data).toBeTruthy()
        expect(result.current.error).toBeNull()
      })

      // Verify API was called correctly
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/research/query'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            query: 'artificial intelligence',
          }),
        })
      )
    })

    it('should handle research errors', async () => {
      const mockFetch = createMockFetchError(new Error('Network error'))
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // Start research
      result.current.submitResearch('test query')

      // Should handle error
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.error).toBeTruthy()
        expect(result.current.data).toBeNull()
      })
    })

    it('should handle retry functionality', async () => {
      const mockFetch = createMockFetchError(new Error('Network error'))
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // Start research (should fail)
      result.current.submitResearch('test query')

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
      })

      // Setup successful response for retry
      const successFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = successFetch

      // Retry
      result.current.retry()

      // Should succeed on retry
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.data).toBeTruthy()
        expect(result.current.error).toBeNull()
      })
    })
  })

  describe('useApiState hook integration', () => {
    it('should manage API state correctly', async () => {
      const mockFetch = createMockFetch({ message: 'Success' })
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useApiState(), { wrapper })

      // Initial state
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()

      // Make API call
      const apiCall = async () => {
        const response = await fetch('/api/test')
        return response.json()
      }

      result.current.executeWithState(apiCall)

      // Should be loading
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true)
      })

      // Should complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.error).toBeNull()
      })
    })

    it('should handle API errors in state', async () => {
      const mockFetch = createMockFetchError(new Error('API Error'))
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useApiState(), { wrapper })

      // Make failing API call
      const apiCall = async () => {
        const response = await fetch('/api/test')
        return response.json()
      }

      result.current.executeWithState(apiCall)

      // Should handle error
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.error).toBeTruthy()
      })
    })
  })

  describe('Query caching integration', () => {
    it('should cache research results', async () => {
      const mockFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = mockFetch

      const wrapper = createWrapper()
      
      // First hook instance
      const { result: result1 } = renderHook(() => useResearch(), { wrapper })
      
      // Submit research
      result1.current.submitResearch('test query')

      await waitFor(() => {
        expect(result1.current.data).toBeTruthy()
      })

      // Second hook instance should use cached data
      const { result: result2 } = renderHook(() => useResearch(), { wrapper })

      // Should have cached data immediately
      expect(result2.current.data).toBeTruthy()
      
      // API should only be called once
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('should invalidate cache on error', async () => {
      const successFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = successFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // First successful call
      result.current.submitResearch('test query')

      await waitFor(() => {
        expect(result.current.data).toBeTruthy()
      })

      // Setup error response
      const errorFetch = createMockFetchError(new Error('Server error'))
      global.fetch = errorFetch

      // Second call should fail and invalidate cache
      result.current.submitResearch('test query 2')

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
      })
    })
  })

  describe('Background refetching', () => {
    it('should refetch data in background', async () => {
      const mockFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // Initial fetch
      result.current.submitResearch('test query')

      await waitFor(() => {
        expect(result.current.data).toBeTruthy()
      })

      // Clear mock to track refetch
      mockFetch.mockClear()

      // Trigger refetch
      result.current.refetch()

      // Should refetch in background
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Optimistic updates', () => {
    it('should handle optimistic updates correctly', async () => {
      const mockFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = mockFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // Submit with optimistic update
      result.current.submitResearch('test query')

      // Should immediately show loading state
      expect(result.current.isLoading).toBe(true)

      // Should complete with actual data
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.data).toBeTruthy()
      })
    })
  })

  describe('Error recovery', () => {
    it('should recover from network errors', async () => {
      // Start with network error
      const errorFetch = createMockFetchError(new Error('Network error'))
      global.fetch = errorFetch

      const wrapper = createWrapper()
      const { result } = renderHook(() => useResearch(), { wrapper })

      // First attempt should fail
      result.current.submitResearch('test query')

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
      })

      // Fix network and retry
      const successFetch = createMockFetch(mockApiResponses.research.success.data)
      global.fetch = successFetch

      result.current.retry()

      // Should recover
      await waitFor(() => {
        expect(result.current.error).toBeNull()
        expect(result.current.data).toBeTruthy()
      })
    })
  })
})