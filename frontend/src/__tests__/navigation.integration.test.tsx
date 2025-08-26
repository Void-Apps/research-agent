import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import Home from '@/app/page';
import HistoryPage from '@/app/history/page';
import ResultsPage from '@/app/results/[id]/page';
import { useSubmitResearch, useResearchHistory, useResearchResults, useResearchStatus } from '@/hooks/useResearch';

// Mock all dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/hooks/useResearch', () => ({
  useSubmitResearch: jest.fn(),
  useResearchHistory: jest.fn(),
  useResearchResults: jest.fn(),
  useResearchStatus: jest.fn(),
}));

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock all layout and UI components
jest.mock('@/components/layout/MainLayout', () => {
  return function MockMainLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="main-layout">{children}</div>;
  };
});

jest.mock('@/components/ResearchForm', () => {
  return function MockResearchForm({ 
    onSubmit, 
    isLoading 
  }: { 
    onSubmit: (query: string) => void; 
    isLoading?: boolean; 
  }) {
    return (
      <div data-testid="research-form">
        <input 
          data-testid="query-input" 
          placeholder="Enter research query"
          onChange={() => {}}
        />
        <button
          onClick={() => onSubmit('test query')}
          disabled={isLoading}
          data-testid="submit-button"
        >
          {isLoading ? 'Loading...' : 'Submit Research'}
        </button>
      </div>
    );
  };
});

jest.mock('@/components/ResultsDisplay', () => {
  return function MockResultsDisplay({ results }: { results: { query_id: string } }) {
    return <div data-testid="results-display">Results for {results.query_id}</div>;
  };
});

jest.mock('@/components/ui/Breadcrumb', () => {
  return function MockBreadcrumb({ items }: { items: Array<{ label: string }> }) {
    return (
      <nav data-testid="breadcrumb">
        {items.map((item, index) => (
          <span key={index}>{item.label}</span>
        ))}
      </nav>
    );
  };
});

jest.mock('@/components/ui/LoadingIndicator', () => {
  return function MockLoadingIndicator() {
    return <div data-testid="loading-indicator">Loading...</div>;
  };
});

jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn(() => '2 hours ago'),
}));

const mockPush = jest.fn();
const mockMutateAsync = jest.fn();

describe('Navigation Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  describe('Home to Results Navigation', () => {
    it('navigates from home to results page after successful submission', async () => {
      const mockResult = { id: 'test-query-id' };
      mockMutateAsync.mockResolvedValue(mockResult);
      
      (useSubmitResearch as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      });

      render(<Home />);
      
      const submitButton = screen.getByTestId('submit-button');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/results/test-query-id');
      });
    });
  });

  describe('History to Results Navigation', () => {
    it('provides links from history page to individual results', () => {
      const mockHistory = [
        {
          id: 'query-1',
          query: 'Machine learning',
          timestamp: '2025-01-01T10:00:00Z',
          status: 'completed' as const,
        },
        {
          id: 'query-2',
          query: 'Quantum computing',
          timestamp: '2025-01-01T09:00:00Z',
          status: 'processing' as const,
        },
      ];

      (useResearchHistory as jest.Mock).mockReturnValue({
        data: mockHistory,
        isLoading: false,
        error: null,
      });

      render(<HistoryPage />);
      
      const link1 = screen.getByRole('link', { name: /Machine learning/ });
      const link2 = screen.getByRole('link', { name: /Quantum computing/ });
      
      expect(link1).toHaveAttribute('href', '/results/query-1');
      expect(link2).toHaveAttribute('href', '/results/query-2');
    });
  });

  describe('Results Page Navigation', () => {
    it('provides navigation back to home and history', () => {
      (useResearchResults as jest.Mock).mockReturnValue({
        data: {
          query_id: 'test-id',
          sources: { google_scholar: [] },
          summary: 'Test summary',
          confidence_score: 0.8,
          cached: false,
        },
        isLoading: false,
        error: null,
      });

      (useResearchStatus as jest.Mock).mockReturnValue({
        data: { status: 'completed' },
        isLoading: false,
      });

      render(<ResultsPage params={{ id: 'test-id' }} />);
      
      const newResearchLink = screen.getByRole('link', { name: 'New Research' });
      const historyLink = screen.getByRole('link', { name: 'View History' });
      
      expect(newResearchLink).toHaveAttribute('href', '/');
      expect(historyLink).toHaveAttribute('href', '/history');
    });

    it('handles navigation on error state', () => {
      (useResearchResults as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Failed'),
      });

      (useResearchStatus as jest.Mock).mockReturnValue({
        data: { status: 'failed' },
        isLoading: false,
      });

      render(<ResultsPage params={{ id: 'test-id' }} />);
      
      const submitNewButton = screen.getByText('Submit New Query');
      fireEvent.click(submitNewButton);
      
      expect(mockPush).toHaveBeenCalledWith('/');
    });
  });

  describe('Breadcrumb Navigation', () => {
    it('renders breadcrumbs on results page', () => {
      (useResearchResults as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      });

      (useResearchStatus as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
      });

      render(<ResultsPage params={{ id: 'test-id' }} />);
      
      expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
      expect(screen.getByText('Research Results')).toBeInTheDocument();
    });

    it('renders breadcrumbs on history page', () => {
      (useResearchHistory as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      });

      render(<HistoryPage />);
      
      expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
      expect(screen.getByText('Research History')).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading state on home page during submission', () => {
      (useSubmitResearch as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
      });

      render(<Home />);
      
      const submitButton = screen.getByTestId('submit-button');
      expect(submitButton).toHaveTextContent('Loading...');
      expect(submitButton).toBeDisabled();
    });

    it('shows loading state on results page', () => {
      (useResearchResults as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      });

      (useResearchStatus as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
      });

      render(<ResultsPage params={{ id: 'test-id' }} />);
      
      expect(screen.getByText('Loading research results...')).toBeInTheDocument();
    });

    it('shows loading state on history page', () => {
      (useResearchHistory as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      });

      render(<HistoryPage />);
      
      expect(screen.getByText('Loading research history...')).toBeInTheDocument();
    });
  });
});