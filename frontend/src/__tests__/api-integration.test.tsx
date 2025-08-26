import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import React from 'react';
import { ResearchAPI } from '@/lib/research-api';
import { useResearchWorkflow } from '@/hooks/useResearch';
import { useApiConnection } from '@/hooks/useApiState';
import { useResearchLoadingStates } from '@/hooks/useLoadingStates';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the ResearchAPI
jest.mock('@/lib/research-api');
const mockResearchAPI = ResearchAPI as jest.Mocked<typeof ResearchAPI>;

// Mock fetch for connection checks
global.fetch = jest.fn();

// Mock toast
jest.mock('@/components/ui/Toast', () => ({
  showToast: jest.fn(),
}));

// Test component that uses the research workflow
function TestResearchComponent({ queryId }: { queryId?: string }) {
  const workflow = useResearchWorkflow(queryId);
  const connection = useApiConnection();
  const loadingStates = useResearchLoadingStates();

  return React.createElement('div', null,
    React.createElement('div', { 'data-testid': 'connection-status' },
      connection.isConnected ? 'Connected' : 'Disconnected'
    ),
    React.createElement('div', { 'data-testid': 'loading-status' },
      workflow.isLoading ? 'Loading' : 'Not Loading'
    ),
    React.createElement('div', { 'data-testid': 'submission-status' },
      loadingStates.isSubmitting ? 'Submitting' : 'Not Submitting'
    ),
    React.createElement('div', { 'data-testid': 'processing-status' },
      loadingStates.isProcessing ? 'Processing' : 'Not Processing'
    ),
    React.createElement('div', { 'data-testid': 'results-status' },
      loadingStates.isLoadingResults ? 'Loading Results' : 'Not Loading Results'
    ),
    React.createElement('button', {
      'data-testid': 'submit-button',
      onClick: () => workflow.submitResearch({ query: 'test query' }),
      disabled: workflow.isSubmitting
    }, 'Submit Research'),
    React.createElement('button', {
      'data-testid': 'invalidate-button',
      onClick: () => workflow.invalidateAll()
    }, 'Invalidate All'),
    React.createElement('button', {
      'data-testid': 'clear-cache-button',
      onClick: () => workflow.clearCache()
    }, 'Clear Cache'),
    workflow.status && React.createElement('div', { 'data-testid': 'status-data' },
      `Status: ${workflow.status.status}${workflow.status.progress ? ` (${workflow.status.progress}%)` : ''}`
    ),
    workflow.results && React.createElement('div', { 'data-testid': 'results-data' },
      `Results: ${workflow.results.summary}`
    ),
    workflow.hasError && React.createElement('div', { 'data-testid': 'error-status' }, 'Has Error'),
    workflow.isComplete && React.createElement('div', { 'data-testid': 'complete-status' }, 'Complete')
  );
}

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

describe('API Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true });
  });

  it('should handle complete research workflow', async () => {
    const mockQuery = {
      id: 'test-id',
      query: 'test query',
      timestamp: '2024-01-01T00:00:00Z',
      status: 'pending' as const,
    };

    const mockStatus = { status: 'processing', progress: 50 };
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

    mockResearchAPI.submitQuery.mockResolvedValue(mockQuery);
    mockResearchAPI.getStatus.mockResolvedValue(mockStatus);
    mockResearchAPI.getResults.mockResolvedValue(mockResults);

    render(<TestResearchComponent />, { wrapper: createWrapper() });

    // Check initial state
    expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected');
    expect(screen.getByTestId('loading-status')).toHaveTextContent('Not Loading');

    // Submit research
    fireEvent.click(screen.getByTestId('submit-button'));

    // Should show submitting state
    await waitFor(() => {
      expect(mockResearchAPI.submitQuery).toHaveBeenCalledWith({ query: 'test query' });
    });
  });

  it('should handle API connection status', async () => {
    // Mock successful connection
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

    render(<TestResearchComponent />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected');
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/health', {
      method: 'HEAD',
      cache: 'no-cache',
    });
  });

  it('should handle connection failures', async () => {
    // Mock connection failure
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<TestResearchComponent />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Disconnected');
    });
  });

  it('should handle research submission errors', async () => {
    const error = new Error('Submission failed');
    mockResearchAPI.submitQuery.mockRejectedValue(error);

    render(<TestResearchComponent />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByTestId('submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('error-status')).toBeInTheDocument();
    });
  });

  it('should handle status and results polling', async () => {
    const mockQuery = {
      id: 'test-id',
      query: 'test query',
      timestamp: '2024-01-01T00:00:00Z',
      status: 'pending' as const,
    };

    const mockStatus = { status: 'completed' };
    const mockResults = {
      query_id: 'test-id',
      sources: {},
      summary: 'Test summary',
      confidence_score: 0.8,
      cached: false,
    };

    mockResearchAPI.getStatus.mockResolvedValue(mockStatus);
    mockResearchAPI.getResults.mockResolvedValue(mockResults);

    render(<TestResearchComponent queryId="test-id" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('status-data')).toHaveTextContent('Status: completed');
      expect(screen.getByTestId('results-data')).toHaveTextContent('Results: Test summary');
      expect(screen.getByTestId('complete-status')).toBeInTheDocument();
    });
  });

  it('should handle cache operations', async () => {
    render(<TestResearchComponent />, { wrapper: createWrapper() });

    // Test invalidate all
    fireEvent.click(screen.getByTestId('invalidate-button'));
    
    // Test clear cache
    fireEvent.click(screen.getByTestId('clear-cache-button'));

    // These operations should not throw errors
    expect(screen.getByTestId('invalidate-button')).toBeInTheDocument();
    expect(screen.getByTestId('clear-cache-button')).toBeInTheDocument();
  });

  it('should handle optimistic updates', async () => {
    const mockQuery = {
      id: 'test-id',
      query: 'test query',
      timestamp: '2024-01-01T00:00:00Z',
      status: 'pending' as const,
    };

    // Delay the API response to test optimistic updates
    mockResearchAPI.submitQuery.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockQuery), 100))
    );

    render(<TestResearchComponent />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByTestId('submit-button'));

    // Should immediately show loading state (optimistic update)
    expect(screen.getByTestId('loading-status')).toHaveTextContent('Loading');

    await waitFor(() => {
      expect(mockResearchAPI.submitQuery).toHaveBeenCalled();
    });
  });

  it('should handle background refetching', async () => {
    const mockStatus = { status: 'processing', progress: 25 };
    mockResearchAPI.getStatus.mockResolvedValue(mockStatus);

    render(<TestResearchComponent queryId="test-id" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('status-data')).toHaveTextContent('Status: processing (25%)');
    });

    // Should continue polling for processing status
    expect(mockResearchAPI.getStatus).toHaveBeenCalledWith('test-id');
  });
});