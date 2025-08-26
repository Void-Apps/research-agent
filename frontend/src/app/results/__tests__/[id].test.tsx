import { render, screen, fireEvent } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import ResultsPage from '../[id]/page';
import { useResearchResults, useResearchStatus } from '@/hooks/useResearch';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/hooks/useResearch', () => ({
  useResearchResults: jest.fn(),
  useResearchStatus: jest.fn(),
}));

jest.mock('@/components/layout/MainLayout', () => {
  return function MockMainLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="main-layout">{children}</div>;
  };
});

jest.mock('@/components/ui/Breadcrumb', () => {
  return function MockBreadcrumb({ items }: { items: Array<{ label: string }> }) {
    return <div data-testid="breadcrumb">{items[0]?.label}</div>;
  };
});

jest.mock('@/components/ResultsDisplay', () => {
  return function MockResultsDisplay({ results }: { results: { query_id: string } }) {
    return <div data-testid="results-display">Results for {results.query_id}</div>;
  };
});

jest.mock('@/components/ui/LoadingIndicator', () => {
  return function MockLoadingIndicator({ size }: { size?: string }) {
    return <div data-testid="loading-indicator" data-size={size}>Loading...</div>;
  };
});

const mockPush = jest.fn();

describe('Results Page', () => {
  const mockParams = { id: 'test-query-id' };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  it('renders loading state', () => {
    (useResearchResults as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });
    (useResearchStatus as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
    });

    render(<ResultsPage params={mockParams} />);
    
    expect(screen.getByText('Loading research results...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('renders processing state', () => {
    (useResearchResults as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });
    (useResearchStatus as jest.Mock).mockReturnValue({
      data: { status: 'processing', progress: 50 },
      isLoading: false,
    });

    render(<ResultsPage params={mockParams} />);
    
    expect(screen.getByText('Research in Progress')).toBeInTheDocument();
    expect(screen.getByText('Gathering information from academic sources...')).toBeInTheDocument();
    expect(screen.getByText('50% complete')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useResearchResults as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load'),
    });
    (useResearchStatus as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
    });

    render(<ResultsPage params={mockParams} />);
    
    expect(screen.getByText('Research Failed')).toBeInTheDocument();
    expect(screen.getByText('There was an error processing your research query. Please try again.')).toBeInTheDocument();
  });

  it('renders results when available', () => {
    const mockResults = {
      query_id: 'test-query-id',
      sources: { google_scholar: [] },
      summary: 'Test summary',
      confidence_score: 0.8,
      cached: false,
    };

    (useResearchResults as jest.Mock).mockReturnValue({
      data: mockResults,
      isLoading: false,
      error: null,
    });
    (useResearchStatus as jest.Mock).mockReturnValue({
      data: { status: 'completed' },
      isLoading: false,
    });

    render(<ResultsPage params={mockParams} />);
    
    expect(screen.getByText('Research Results')).toBeInTheDocument();
    expect(screen.getByText('test-query-id')).toBeInTheDocument();
    expect(screen.getByTestId('results-display')).toBeInTheDocument();
  });

  it('handles navigation to new research', () => {
    (useResearchResults as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });
    (useResearchStatus as jest.Mock).mockReturnValue({
      data: { status: 'failed' },
      isLoading: false,
    });

    render(<ResultsPage params={mockParams} />);
    
    const submitNewButton = screen.getByText('Submit New Query');
    fireEvent.click(submitNewButton);
    
    expect(mockPush).toHaveBeenCalledWith('/');
  });

  it('renders breadcrumb navigation', () => {
    (useResearchResults as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });
    (useResearchStatus as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
    });

    render(<ResultsPage params={mockParams} />);
    
    expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
    expect(screen.getByText('Research Results')).toBeInTheDocument();
  });
});