import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResultsDisplay from '../ResultsDisplay';
import { ResearchResult, SourceResult } from '@/lib/types';

// Mock the child components
jest.mock('../results', () => ({
  ScholarResults: ({ results, isExpanded, onToggle }: any) => (
    <div data-testid="scholar-results">
      <button onClick={onToggle} data-testid="scholar-toggle">
        Scholar Results ({results.length}) - {isExpanded ? 'Expanded' : 'Collapsed'}
      </button>
    </div>
  ),
  BooksResults: ({ results, isExpanded, onToggle }: any) => (
    <div data-testid="books-results">
      <button onClick={onToggle} data-testid="books-toggle">
        Books Results ({results.length}) - {isExpanded ? 'Expanded' : 'Collapsed'}
      </button>
    </div>
  ),
  ScienceDirectResults: ({ results, isExpanded, onToggle }: any) => (
    <div data-testid="sciencedirect-results">
      <button onClick={onToggle} data-testid="sciencedirect-toggle">
        ScienceDirect Results ({results.length}) - {isExpanded ? 'Expanded' : 'Collapsed'}
      </button>
    </div>
  ),
}));

const mockScholarResult: SourceResult = {
  title: 'Test Scholar Paper',
  authors: ['John Doe', 'Jane Smith'],
  abstract: 'This is a test abstract for a scholar paper.',
  url: 'https://scholar.google.com/test',
  publication_date: '2023-01-01',
  source_type: 'google_scholar',
  citation_count: 42,
};

const mockBookResult: SourceResult = {
  title: 'Test Book',
  authors: ['Author One'],
  abstract: 'This is a test book description.',
  url: 'https://books.google.com/test',
  publication_date: '2022-06-15',
  source_type: 'google_books',
  isbn: '9781234567890',
  preview_link: 'https://books.google.com/preview/test',
};

const mockScienceDirectResult: SourceResult = {
  title: 'Test Scientific Paper',
  authors: ['Dr. Science', 'Prof. Research'],
  abstract: 'This is a test abstract for a scientific paper.',
  url: 'https://sciencedirect.com/test',
  publication_date: '2023-03-15',
  source_type: 'sciencedirect',
  doi: '10.1016/j.test.2023.01.001',
  journal: 'Journal of Test Sciences',
};

const mockResults: ResearchResult = {
  query_id: 'test-query-123',
  sources: {
    google_scholar: [mockScholarResult],
    google_books: [mockBookResult],
    sciencedirect: [mockScienceDirectResult],
  },
  summary: 'This is a comprehensive research summary covering multiple academic sources.',
  confidence_score: 0.85,
  cached: false,
};

describe('ResultsDisplay', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('renders loading indicator when isLoading is true', () => {
      render(<ResultsDisplay isLoading={true} />);
      
      expect(screen.getByText('Searching academic sources...')).toBeInTheDocument();
      expect(screen.getByText('This may take a few moments as we search multiple databases')).toBeInTheDocument();
      expect(screen.getByText('Google Scholar')).toBeInTheDocument();
      expect(screen.getByText('Google Books')).toBeInTheDocument();
      expect(screen.getByText('ScienceDirect')).toBeInTheDocument();
    });

    it('shows progress indicators for each source during loading', () => {
      render(<ResultsDisplay isLoading={true} />);
      
      // Check for source icons and names
      expect(screen.getByText('🎓')).toBeInTheDocument();
      expect(screen.getByText('📚')).toBeInTheDocument();
      expect(screen.getByText('🔬')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('renders error message when error prop is provided', () => {
      const errorMessage = 'Failed to fetch research results';
      render(<ResultsDisplay error={errorMessage} />);
      
      expect(screen.getByText('Research Failed')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  describe('No Results State', () => {
    it('renders no results message when results is undefined', () => {
      render(<ResultsDisplay />);
      
      expect(screen.getByText('No Research Results')).toBeInTheDocument();
      expect(screen.getByText('Submit a research query to see results here.')).toBeInTheDocument();
    });

    it('renders no results found message when all sources are empty', () => {
      const emptyResults: ResearchResult = {
        ...mockResults,
        sources: {
          google_scholar: [],
          google_books: [],
          sciencedirect: [],
        },
      };
      
      render(<ResultsDisplay results={emptyResults} />);
      
      expect(screen.getByText('No Results Found')).toBeInTheDocument();
      expect(screen.getByText(/We couldn't find any results for your research query/)).toBeInTheDocument();
    });
  });

  describe('Results Display', () => {
    it('renders research results header with correct information', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      expect(screen.getByText('Research Results')).toBeInTheDocument();
      expect(screen.getByText('3 results found')).toBeInTheDocument();
      expect(screen.getByText('85% confidence')).toBeInTheDocument();
    });

    it('shows cached indicator when results are cached', () => {
      const cachedResults = { ...mockResults, cached: true };
      render(<ResultsDisplay results={cachedResults} />);
      
      expect(screen.getByText('Cached results')).toBeInTheDocument();
    });

    it('renders AI summary section', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      expect(screen.getByText('AI Research Summary')).toBeInTheDocument();
      expect(screen.getByText(mockResults.summary)).toBeInTheDocument();
    });

    it('renders source components when results are available', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      expect(screen.getByTestId('scholar-results')).toBeInTheDocument();
      expect(screen.getByTestId('books-results')).toBeInTheDocument();
      expect(screen.getByTestId('sciencedirect-results')).toBeInTheDocument();
    });

    it('does not render source components when no results for that source', () => {
      const partialResults: ResearchResult = {
        ...mockResults,
        sources: {
          google_scholar: [mockScholarResult],
          google_books: [],
          sciencedirect: undefined,
        },
      };
      
      render(<ResultsDisplay results={partialResults} />);
      
      expect(screen.getByTestId('scholar-results')).toBeInTheDocument();
      expect(screen.queryByTestId('books-results')).not.toBeInTheDocument();
      expect(screen.queryByTestId('sciencedirect-results')).not.toBeInTheDocument();
    });
  });

  describe('Expandable Sections', () => {
    it('toggles summary section when clicked', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      const summaryToggle = screen.getByRole('button', { name: /AI Research Summary/ });
      
      // Summary should be expanded by default
      expect(screen.getByText(mockResults.summary)).toBeInTheDocument();
      
      // Click to collapse
      fireEvent.click(summaryToggle);
      expect(screen.queryByText(mockResults.summary)).not.toBeInTheDocument();
      
      // Click to expand again
      fireEvent.click(summaryToggle);
      expect(screen.getByText(mockResults.summary)).toBeInTheDocument();
    });

    it('passes correct expansion state to child components', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      // Initially collapsed (except summary)
      expect(screen.getByText(/Scholar Results \(1\) - Collapsed/)).toBeInTheDocument();
      expect(screen.getByText(/Books Results \(1\) - Collapsed/)).toBeInTheDocument();
      expect(screen.getByText(/ScienceDirect Results \(1\) - Collapsed/)).toBeInTheDocument();
    });

    it('toggles child component sections independently', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      const scholarToggle = screen.getByTestId('scholar-toggle');
      const booksToggle = screen.getByTestId('books-toggle');
      
      // Expand scholar results
      fireEvent.click(scholarToggle);
      expect(screen.getByText(/Scholar Results \(1\) - Expanded/)).toBeInTheDocument();
      expect(screen.getByText(/Books Results \(1\) - Collapsed/)).toBeInTheDocument();
      
      // Expand books results
      fireEvent.click(booksToggle);
      expect(screen.getByText(/Scholar Results \(1\) - Expanded/)).toBeInTheDocument();
      expect(screen.getByText(/Books Results \(1\) - Expanded/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes for expandable sections', () => {
      render(<ResultsDisplay results={mockResults} />);
      
      const summaryToggle = screen.getByRole('button', { name: /AI Research Summary/ });
      expect(summaryToggle).toHaveAttribute('aria-expanded', 'true');
    });

    it('applies custom className when provided', () => {
      const { container } = render(
        <ResultsDisplay results={mockResults} className="custom-class" />
      );
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Edge Cases', () => {
    it('handles missing summary gracefully', () => {
      const resultsWithoutSummary = { ...mockResults, summary: '' };
      render(<ResultsDisplay results={resultsWithoutSummary} />);
      
      expect(screen.getByText('AI Research Summary')).toBeInTheDocument();
    });

    it('handles zero confidence score', () => {
      const resultsWithZeroConfidence = { ...mockResults, confidence_score: 0 };
      render(<ResultsDisplay results={resultsWithZeroConfidence} />);
      
      expect(screen.getByText('0% confidence')).toBeInTheDocument();
    });

    it('handles undefined sources gracefully', () => {
      const resultsWithUndefinedSources: ResearchResult = {
        ...mockResults,
        sources: {} as any,
      };
      
      render(<ResultsDisplay results={resultsWithUndefinedSources} />);
      
      expect(screen.getByText('0 results found')).toBeInTheDocument();
    });
  });
});