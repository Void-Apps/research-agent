/**
 * Simple routing tests to verify page structure and navigation elements
 */

import { render, screen } from '@testing-library/react';

// Mock Next.js components
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

jest.mock('next/link', () => {
  return function MockLink({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
    return <a href={href} className={className}>{children}</a>;
  };
});

// Mock all hooks to avoid dependency issues
jest.mock('@/hooks/useResearch', () => ({
  useSubmitResearch: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useResearchHistory: () => ({
    data: [],
    isLoading: false,
    error: null,
  }),
  useResearchResults: () => ({
    data: null,
    isLoading: false,
    error: null,
  }),
  useResearchStatus: () => ({
    data: null,
    isLoading: false,
  }),
}));

// Mock toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock all components to focus on routing structure
jest.mock('@/components/layout/MainLayout', () => {
  return function MockMainLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="main-layout">{children}</div>;
  };
});

jest.mock('@/components/ResearchForm', () => {
  return function MockResearchForm() {
    return <div data-testid="research-form">Research Form</div>;
  };
});

jest.mock('@/components/ResultsDisplay', () => {
  return function MockResultsDisplay() {
    return <div data-testid="results-display">Results Display</div>;
  };
});

jest.mock('@/components/ui/Breadcrumb', () => {
  return function MockBreadcrumb({ items }: { items: Array<{ label: string }> }) {
    return <div data-testid="breadcrumb">{items[0]?.label}</div>;
  };
});

jest.mock('@/components/ui/LoadingIndicator', () => {
  return function MockLoadingIndicator() {
    return <div data-testid="loading-indicator">Loading</div>;
  };
});

jest.mock('date-fns', () => ({
  formatDistanceToNow: () => '2 hours ago',
}));

describe('Page Routing and Structure', () => {
  describe('Home Page', () => {
    it('renders home page with correct structure', async () => {
      const Home = (await import('@/app/page')).default;
      render(<Home />);
      
      expect(screen.getByText('AI Research Agent')).toBeInTheDocument();
      expect(screen.getByText(/Submit your research requirements/)).toBeInTheDocument();
      expect(screen.getByTestId('research-form')).toBeInTheDocument();
    });
  });

  describe('History Page', () => {
    it('renders history page with correct structure', async () => {
      const HistoryPage = (await import('@/app/history/page')).default;
      render(<HistoryPage />);
      
      expect(screen.getByText('Research History')).toBeInTheDocument();
      expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
      expect(screen.getByText('Research History')).toBeInTheDocument();
    });

    it('has navigation link to new research', async () => {
      const HistoryPage = (await import('@/app/history/page')).default;
      render(<HistoryPage />);
      
      const newResearchLink = screen.getByRole('link', { name: 'New Research' });
      expect(newResearchLink).toHaveAttribute('href', '/');
    });
  });

  describe('Results Page', () => {
    it('renders results page with correct structure', async () => {
      const ResultsPage = (await import('@/app/results/[id]/page')).default;
      render(<ResultsPage params={{ id: 'test-id' }} />);
      
      expect(screen.getByText('Research Results')).toBeInTheDocument();
      expect(screen.getByText('test-id')).toBeInTheDocument();
      expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
    });

    it('has navigation links to home and history', async () => {
      const ResultsPage = (await import('@/app/results/[id]/page')).default;
      render(<ResultsPage params={{ id: 'test-id' }} />);
      
      const newResearchLink = screen.getByRole('link', { name: 'New Research' });
      const historyLink = screen.getByRole('link', { name: 'View History' });
      
      expect(newResearchLink).toHaveAttribute('href', '/');
      expect(historyLink).toHaveAttribute('href', '/history');
    });
  });

  describe('Breadcrumb Component', () => {
    it('renders breadcrumb with home link', async () => {
      const Breadcrumb = (await import('@/components/ui/Breadcrumb')).default;
      const items = [{ label: 'Test Page', current: true }];
      
      render(<Breadcrumb items={items} />);
      
      const homeLink = screen.getByRole('link');
      expect(homeLink).toHaveAttribute('href', '/');
    });
  });
});