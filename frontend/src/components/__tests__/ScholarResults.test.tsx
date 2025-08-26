import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ScholarResults from '../results/ScholarResults';
import { SourceResult } from '@/lib/types';

const mockScholarResults: SourceResult[] = [
  {
    title: 'Machine Learning Applications in Healthcare',
    authors: ['John Doe', 'Jane Smith', 'Bob Johnson'],
    abstract: 'This paper explores the various applications of machine learning in healthcare, including diagnostic imaging, drug discovery, and personalized treatment plans. The research demonstrates significant improvements in accuracy and efficiency.',
    url: 'https://scholar.google.com/paper1',
    publication_date: '2023-01-15',
    source_type: 'google_scholar',
    citation_count: 142,
  },
  {
    title: 'Deep Learning for Medical Image Analysis',
    authors: ['Alice Wilson'],
    abstract: 'A comprehensive study on deep learning techniques for medical image analysis.',
    url: 'https://scholar.google.com/paper2',
    publication_date: '2022-12-01',
    source_type: 'google_scholar',
    citation_count: 89,
  },
  {
    title: 'AI Ethics in Healthcare Systems',
    authors: ['Dr. Ethics', 'Prof. Morality'],
    abstract: 'This research examines the ethical implications of artificial intelligence implementation in healthcare systems, focusing on patient privacy, algorithmic bias, and decision-making transparency.',
    publication_date: '2023-03-20',
    source_type: 'google_scholar',
    citation_count: 23,
  },
];

const mockProps = {
  results: mockScholarResults,
  isExpanded: false,
  onToggle: jest.fn(),
};

describe('ScholarResults', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Header Section', () => {
    it('renders header with correct title and count', () => {
      render(<ScholarResults {...mockProps} />);
      
      expect(screen.getByText('Google Scholar')).toBeInTheDocument();
      expect(screen.getByText('3 academic papers found')).toBeInTheDocument();
      expect(screen.getByText('🎓')).toBeInTheDocument();
    });

    it('shows singular form when only one result', () => {
      render(<ScholarResults {...mockProps} results={[mockScholarResults[0]]} />);
      
      expect(screen.getByText('1 academic paper found')).toBeInTheDocument();
    });

    it('calls onToggle when header is clicked', () => {
      render(<ScholarResults {...mockProps} />);
      
      const headerButton = screen.getByRole('button');
      fireEvent.click(headerButton);
      
      expect(mockProps.onToggle).toHaveBeenCalledTimes(1);
    });

    it('shows correct expand/collapse text', () => {
      const { rerender } = render(<ScholarResults {...mockProps} isExpanded={false} />);
      expect(screen.getByText('Show results')).toBeInTheDocument();
      
      rerender(<ScholarResults {...mockProps} isExpanded={true} />);
      expect(screen.getByText('Hide results')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<ScholarResults {...mockProps} isExpanded={true} />);
      
      const headerButton = screen.getByRole('button');
      expect(headerButton).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Collapsed State', () => {
    it('does not show results when collapsed', () => {
      render(<ScholarResults {...mockProps} isExpanded={false} />);
      
      expect(screen.queryByText(mockScholarResults[0].title)).not.toBeInTheDocument();
      expect(screen.queryByText(mockScholarResults[0].abstract!)).not.toBeInTheDocument();
    });
  });

  describe('Expanded State', () => {
    const expandedProps = { ...mockProps, isExpanded: true };

    it('shows all results when expanded', () => {
      render(<ScholarResults {...expandedProps} />);
      
      mockScholarResults.forEach(result => {
        expect(screen.getByText(result.title)).toBeInTheDocument();
      });
    });

    it('renders paper titles as clickable links when URL is provided', () => {
      render(<ScholarResults {...expandedProps} />);
      
      const titleLink = screen.getByRole('link', { name: mockScholarResults[0].title });
      expect(titleLink).toHaveAttribute('href', mockScholarResults[0].url);
      expect(titleLink).toHaveAttribute('target', '_blank');
      expect(titleLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders paper titles as plain text when no URL', () => {
      const resultsWithoutUrl = [{ ...mockScholarResults[0], url: undefined }];
      render(<ScholarResults {...expandedProps} results={resultsWithoutUrl} />);
      
      expect(screen.getByText(mockScholarResults[0].title)).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: mockScholarResults[0].title })).not.toBeInTheDocument();
    });

    it('formats authors correctly', () => {
      render(<ScholarResults {...expandedProps} />);
      
      // Multiple authors (>2) should show "First Author et al."
      expect(screen.getByText('John Doe et al.')).toBeInTheDocument();
      
      // Single author should show full name
      expect(screen.getByText('Alice Wilson')).toBeInTheDocument();
      
      // Two authors should show "Author1 and Author2"
      expect(screen.getByText('Dr. Ethics and Prof. Morality')).toBeInTheDocument();
    });

    it('formats publication dates correctly', () => {
      render(<ScholarResults {...expandedProps} />);
      
      expect(screen.getAllByText('2023')).toHaveLength(2); // Two papers from 2023
      expect(screen.getByText('2022')).toBeInTheDocument();
    });

    it('displays citation counts', () => {
      render(<ScholarResults {...expandedProps} />);
      
      expect(screen.getByText('142 citations')).toBeInTheDocument();
      expect(screen.getByText('89 citations')).toBeInTheDocument();
      expect(screen.getByText('23 citations')).toBeInTheDocument();
    });

    it('shows abstracts when available', () => {
      render(<ScholarResults {...expandedProps} />);
      
      mockScholarResults.forEach(result => {
        if (result.abstract) {
          expect(screen.getByText(result.abstract, { exact: false })).toBeInTheDocument();
        }
      });
    });

    it('truncates long abstracts', () => {
      const longAbstract = 'A'.repeat(400);
      const resultWithLongAbstract = [{ ...mockScholarResults[0], abstract: longAbstract }];
      
      render(<ScholarResults {...expandedProps} results={resultWithLongAbstract} />);
      
      expect(screen.getByText(/A+\.\.\./)).toBeInTheDocument();
    });

    it('shows appropriate badges', () => {
      render(<ScholarResults {...expandedProps} />);
      
      expect(screen.getAllByText('Academic Paper')).toHaveLength(3);
      expect(screen.getAllByText('Highly Cited')).toHaveLength(2); // Papers with >50 citations
    });

    it('renders View Paper links when URL is available', () => {
      render(<ScholarResults {...expandedProps} />);
      
      const viewPaperLinks = screen.getAllByText('View Paper');
      expect(viewPaperLinks).toHaveLength(2); // Only first two results have URLs
      
      viewPaperLinks.forEach((link, index) => {
        expect(link.closest('a')).toHaveAttribute('href', mockScholarResults[index].url);
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles empty results array', () => {
      render(<ScholarResults {...mockProps} results={[]} />);
      
      expect(screen.getByText('0 academic papers found')).toBeInTheDocument();
    });

    it('handles missing authors', () => {
      const resultWithoutAuthors = [{ ...mockScholarResults[0], authors: [] }];
      render(<ScholarResults {...mockProps} results={resultWithoutAuthors} isExpanded={true} />);
      
      expect(screen.getByText('Authors not available')).toBeInTheDocument();
    });

    it('handles missing publication date', () => {
      const resultWithoutDate = [{ ...mockScholarResults[0], publication_date: undefined }];
      render(<ScholarResults {...mockProps} results={resultWithoutDate} isExpanded={true} />);
      
      expect(screen.getByText('Date not available')).toBeInTheDocument();
    });

    it('handles invalid publication date', () => {
      const resultWithInvalidDate = [{ ...mockScholarResults[0], publication_date: 'invalid-date' }];
      render(<ScholarResults {...mockProps} results={resultWithInvalidDate} isExpanded={true} />);
      
      expect(screen.getByText('invalid-date')).toBeInTheDocument();
    });

    it('handles missing citation count', () => {
      const resultWithoutCitations = [{ ...mockScholarResults[0], citation_count: undefined }];
      render(<ScholarResults {...mockProps} results={resultWithoutCitations} isExpanded={true} />);
      
      expect(screen.queryByText(/citations/)).not.toBeInTheDocument();
    });

    it('handles missing abstract', () => {
      const resultWithoutAbstract = [{ ...mockScholarResults[0], abstract: undefined }];
      render(<ScholarResults {...mockProps} results={resultWithoutAbstract} isExpanded={true} />);
      
      expect(screen.getByText(mockScholarResults[0].title)).toBeInTheDocument();
      // Should not crash and should still render other content
    });

    it('does not show Highly Cited badge for papers with low citations', () => {
      const lowCitationResult = [{ ...mockScholarResults[0], citation_count: 10 }];
      render(<ScholarResults {...mockProps} results={lowCitationResult} isExpanded={true} />);
      
      expect(screen.getByText('Academic Paper')).toBeInTheDocument();
      expect(screen.queryByText('Highly Cited')).not.toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('applies correct CSS classes for visual hierarchy', () => {
      render(<ScholarResults {...mockProps} isExpanded={true} />);
      
      const headerButton = screen.getByRole('button');
      expect(headerButton).toHaveClass('hover:bg-gray-50');
      
      const results = screen.getByText(mockScholarResults[0].title).closest('.border-l-4');
      expect(results).toHaveClass('border-l-4', 'border-blue-500');
    });

    it('shows correct chevron rotation based on expansion state', () => {
      const { rerender } = render(<ScholarResults {...mockProps} isExpanded={false} />);
      
      let chevron = screen.getByRole('button').querySelector('svg');
      expect(chevron).not.toHaveClass('rotate-180');
      
      rerender(<ScholarResults {...mockProps} isExpanded={true} />);
      chevron = screen.getByRole('button').querySelector('svg');
      expect(chevron).toHaveClass('rotate-180');
    });
  });
});