import { render, screen } from '@testing-library/react';
import HistoryPage from '../page';
import { useResearchHistory } from '@/hooks/useResearch';

// Mock dependencies
jest.mock('@/hooks/useResearch', () => ({
  useResearchHistory: jest.fn(),
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

jest.mock('@/components/ui/LoadingIndicator', () => {
  return function MockLoadingIndicator() {
    return <div data-testid="loading-indicator">Loading...</div>;
  };
});

jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn(() => '2 hours ago'),
}));

describe('History Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useResearchHistory as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<HistoryPage />);
    
    expect(screen.getByText('Loading research history...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useResearchHistory as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load'),
    });

    render(<HistoryPage />);
    
    expect(screen.getByText('Failed to Load History')).toBeInTheDocument();
    expect(screen.getByText('There was an error loading your research history. Please try again.')).toBeInTheDocument();
  });

  it('renders empty state when no history', () => {
    (useResearchHistory as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    render(<HistoryPage />);
    
    expect(screen.getByText('No research history')).toBeInTheDocument();
    expect(screen.getByText('Get started by submitting your first research query.')).toBeInTheDocument();
    expect(screen.getByText('Start Research')).toBeInTheDocument();
  });

  it('renders history list when data is available', () => {
    const mockHistory = [
      {
        id: '1',
        query: 'Machine learning algorithms',
        timestamp: '2025-01-01T10:00:00Z',
        status: 'completed' as const,
      },
      {
        id: '2',
        query: 'Quantum computing research',
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
    
    expect(screen.getByText('Research History')).toBeInTheDocument();
    expect(screen.getByText('Machine learning algorithms')).toBeInTheDocument();
    expect(screen.getByText('Quantum computing research')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Processing')).toBeInTheDocument();
  });

  it('renders correct status colors and text', () => {
    const mockHistory = [
      {
        id: '1',
        query: 'Test query 1',
        timestamp: '2025-01-01T10:00:00Z',
        status: 'completed' as const,
      },
      {
        id: '2',
        query: 'Test query 2',
        timestamp: '2025-01-01T09:00:00Z',
        status: 'failed' as const,
      },
      {
        id: '3',
        query: 'Test query 3',
        timestamp: '2025-01-01T08:00:00Z',
        status: 'pending' as const,
      },
    ];

    (useResearchHistory as jest.Mock).mockReturnValue({
      data: mockHistory,
      isLoading: false,
      error: null,
    });

    render(<HistoryPage />);
    
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders breadcrumb navigation', () => {
    (useResearchHistory as jest.Mock).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    render(<HistoryPage />);
    
    expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
    expect(screen.getByText('Research History')).toBeInTheDocument();
  });

  it('has links to individual results', () => {
    const mockHistory = [
      {
        id: 'test-id',
        query: 'Test query',
        timestamp: '2025-01-01T10:00:00Z',
        status: 'completed' as const,
      },
    ];

    (useResearchHistory as jest.Mock).mockReturnValue({
      data: mockHistory,
      isLoading: false,
      error: null,
    });

    render(<HistoryPage />);
    
    const link = screen.getByRole('link', { name: /Test query/ });
    expect(link).toHaveAttribute('href', '/results/test-id');
  });
});