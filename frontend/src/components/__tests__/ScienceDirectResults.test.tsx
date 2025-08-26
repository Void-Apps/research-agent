import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ScienceDirectResults from '../results/ScienceDirectResults';
import { SourceResult } from '@/lib/types';

const mockScienceDirectResults: SourceResult[] = [
  {
    title: 'Machine learning applications in drug discovery and development',
    authors: ['John Smith', 'Maria Garcia', 'David Chen', 'Sarah Johnson', 'Michael Brown'],
    abstract: 'This comprehensive review examines the current state and future prospects of machine learning applications in pharmaceutical research. We discuss various ML techniques including deep learning, reinforcement learning, and ensemble methods in the context of drug discovery, molecular design, and clinical trial optimization.',
    url: 'https://sciencedirect.com/science/article/pii/S1234567890',
    publication_date: '2023-06-15',
    source_type: 'sciencedirect',
    doi: '10.1016/j.drudis.2023.103621',
    journal: 'Drug Discovery Today',
  },
  {
    title: 'Deep neural networks for medical image segmentation',
    authors: ['Alice Wang', 'Bob Thompson'],
    abstract: 'We present a novel approach using convolutional neural networks for automated medical image segmentation with applications in radiology and pathology.',
    url: 'https://sciencedirect.com/science/article/pii/S0987654321',
    publication_date: '2023-03-22',
    source_type: 'sciencedirect',
    doi: 'https://doi.org/10.1016/j.media.2023.102789',
    journal: 'Medical Image Analysis',
  },
  {
    title: 'Artificial intelligence in healthcare: Current applications and future directions',
    authors: ['Dr. Innovation'],
    abstract: 'An overview of AI applications in healthcare including diagnostic systems, treatment planning, and patient monitoring.',
    publication_date: '2023-01-10',
    source_type: 'sciencedirect',
    journal: 'Journal of Medical Systems',
  },
];

const mockProps = {
  results: mockScienceDirectResults,
  isExpanded: false,
  onToggle: jest.fn(),
};

describe('ScienceDirectResults', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Header Section', () => {
    it('renders header with correct title and count', () => {
      render(<ScienceDirectResults {...mockProps} />);
      
      expect(screen.getByText('ScienceDirect')).toBeInTheDocument();
      expect(screen.getByText('3 scientific papers found')).toBeInTheDocument();
      expect(screen.getByText('🔬')).toBeInTheDocument();
    });

    it('shows singular form when only one result', () => {
      render(<ScienceDirectResults {...mockProps} results={[mockScienceDirectResults[0]]} />);
      
      expect(screen.getByText('1 scientific paper found')).toBeInTheDocument();
    });

    it('calls onToggle when header is clicked', () => {
      render(<ScienceDirectResults {...mockProps} />);
      
      const headerButton = screen.getByRole('button');
      fireEvent.click(headerButton);
      
      expect(mockProps.onToggle).toHaveBeenCalledTimes(1);
    });

    it('shows correct expand/collapse text', () => {
      const { rerender } = render(<ScienceDirectResults {...mockProps} isExpanded={false} />);
      expect(screen.getByText('Show results')).toBeInTheDocument();
      
      rerender(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      expect(screen.getByText('Hide results')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      
      const headerButton = screen.getByRole('button');
      expect(headerButton).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Collapsed State', () => {
    it('does not show results when collapsed', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={false} />);
      
      expect(screen.queryByText(mockScienceDirectResults[0].title)).not.toBeInTheDocument();
      expect(screen.queryByText(mockScienceDirectResults[0].abstract!)).not.toBeInTheDocument();
    });
  });

  describe('Expanded State', () => {
    const expandedProps = { ...mockProps, isExpanded: true };

    it('shows all results when expanded', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      mockScienceDirectResults.forEach(result => {
        expect(screen.getByText(result.title)).toBeInTheDocument();
      });
    });

    it('renders paper titles as clickable links when URL is provided', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      const titleLink = screen.getByRole('link', { name: mockScienceDirectResults[0].title });
      expect(titleLink).toHaveAttribute('href', mockScienceDirectResults[0].url);
      expect(titleLink).toHaveAttribute('target', '_blank');
      expect(titleLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders paper titles as plain text when no URL', () => {
      const resultsWithoutUrl = [{ ...mockScienceDirectResults[2] }]; // Third paper has no URL
      render(<ScienceDirectResults {...expandedProps} results={resultsWithoutUrl} />);
      
      expect(screen.getByText(mockScienceDirectResults[2].title)).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: mockScienceDirectResults[2].title })).not.toBeInTheDocument();
    });

    it('formats authors correctly', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      // Many authors (>4) should show "First Author et al."
      expect(screen.getByText('John Smith et al.')).toBeInTheDocument();
      
      // Two authors should show "Author1 and Author2"
      expect(screen.getByText('Alice Wang and Bob Thompson')).toBeInTheDocument();
      
      // Single author should show full name
      expect(screen.getByText('Dr. Innovation')).toBeInTheDocument();
    });

    it('formats publication dates correctly', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      expect(screen.getByText('Jun 15, 2023')).toBeInTheDocument();
      expect(screen.getByText('Mar 22, 2023')).toBeInTheDocument();
      expect(screen.getByText('Jan 10, 2023')).toBeInTheDocument();
    });

    it('displays journal names when available', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      expect(screen.getByText('Drug Discovery Today')).toBeInTheDocument();
      expect(screen.getByText('Medical Image Analysis')).toBeInTheDocument();
      expect(screen.getByText('Journal of Medical Systems')).toBeInTheDocument();
    });

    it('displays DOI when available', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      expect(screen.getByText('DOI: 10.1016/j.drudis.2023.103621')).toBeInTheDocument();
      expect(screen.getByText('DOI: 10.1016/j.media.2023.102789')).toBeInTheDocument();
    });

    it('shows abstracts when available', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      mockScienceDirectResults.forEach(result => {
        if (result.abstract) {
          expect(screen.getByText(result.abstract, { exact: false })).toBeInTheDocument();
        }
      });
    });

    it('truncates long abstracts', () => {
      const longAbstract = 'A'.repeat(450);
      const resultWithLongAbstract = [{ ...mockScienceDirectResults[0], abstract: longAbstract }];
      
      render(<ScienceDirectResults {...expandedProps} results={resultWithLongAbstract} />);
      
      expect(screen.getByText(/A+\.\.\./)).toBeInTheDocument();
    });

    it('shows appropriate badges', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      expect(screen.getAllByText('Scientific Paper')).toHaveLength(3);
      expect(screen.getAllByText('Peer Reviewed')).toHaveLength(3); // All have journals
      expect(screen.getAllByText('DOI Available')).toHaveLength(2); // First two have DOIs
    });

    it('renders DOI links when available', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      const doiLinks = screen.getAllByText('DOI Link');
      expect(doiLinks).toHaveLength(2);
      
      expect(doiLinks[0].closest('a')).toHaveAttribute('href', 'https://doi.org/10.1016/j.drudis.2023.103621');
      expect(doiLinks[1].closest('a')).toHaveAttribute('href', 'https://doi.org/10.1016/j.media.2023.102789');
    });

    it('renders View Paper links when URL is available', () => {
      render(<ScienceDirectResults {...expandedProps} />);
      
      const viewPaperLinks = screen.getAllByText('View Paper');
      expect(viewPaperLinks).toHaveLength(2); // Only first two papers have URLs
      
      expect(viewPaperLinks[0].closest('a')).toHaveAttribute('href', mockScienceDirectResults[0].url);
      expect(viewPaperLinks[1].closest('a')).toHaveAttribute('href', mockScienceDirectResults[1].url);
    });
  });

  describe('DOI Formatting and Links', () => {
    it('cleans DOI prefixes correctly', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      
      // Should remove https://doi.org/ prefix from display
      expect(screen.getByText('DOI: 10.1016/j.media.2023.102789')).toBeInTheDocument();
    });

    it('creates correct DOI URLs', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      
      const doiLinks = screen.getAllByText('DOI Link');
      expect(doiLinks[1].closest('a')).toHaveAttribute('href', 'https://doi.org/10.1016/j.media.2023.102789');
    });

    it('handles DOI without prefix', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      
      expect(screen.getByText('DOI: 10.1016/j.drudis.2023.103621')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty results array', () => {
      render(<ScienceDirectResults {...mockProps} results={[]} />);
      
      expect(screen.getByText('0 scientific papers found')).toBeInTheDocument();
    });

    it('handles missing authors', () => {
      const resultWithoutAuthors = [{ ...mockScienceDirectResults[0], authors: [] }];
      render(<ScienceDirectResults {...mockProps} results={resultWithoutAuthors} isExpanded={true} />);
      
      expect(screen.getByText('Authors not available')).toBeInTheDocument();
    });

    it('handles missing publication date', () => {
      const resultWithoutDate = [{ ...mockScienceDirectResults[0], publication_date: undefined }];
      render(<ScienceDirectResults {...mockProps} results={resultWithoutDate} isExpanded={true} />);
      
      expect(screen.getByText('Date not available')).toBeInTheDocument();
    });

    it('handles invalid publication date', () => {
      const resultWithInvalidDate = [{ ...mockScienceDirectResults[0], publication_date: 'invalid-date' }];
      render(<ScienceDirectResults {...mockProps} results={resultWithInvalidDate} isExpanded={true} />);
      
      expect(screen.getByText('invalid-date')).toBeInTheDocument();
    });

    it('handles missing journal', () => {
      const resultWithoutJournal = [{ ...mockScienceDirectResults[0], journal: undefined }];
      render(<ScienceDirectResults {...mockProps} results={resultWithoutJournal} isExpanded={true} />);
      
      expect(screen.queryByText('Drug Discovery Today')).not.toBeInTheDocument();
      expect(screen.getByText('Scientific Paper')).toBeInTheDocument();
      expect(screen.queryByText('Peer Reviewed')).not.toBeInTheDocument();
    });

    it('handles missing DOI', () => {
      const resultWithoutDOI = [{ ...mockScienceDirectResults[2] }]; // Third paper has no DOI
      render(<ScienceDirectResults {...mockProps} results={resultWithoutDOI} isExpanded={true} />);
      
      expect(screen.queryByText(/DOI:/)).not.toBeInTheDocument();
      expect(screen.queryByText('DOI Available')).not.toBeInTheDocument();
      expect(screen.queryByText('DOI Link')).not.toBeInTheDocument();
    });

    it('handles missing abstract', () => {
      const resultWithoutAbstract = [{ ...mockScienceDirectResults[0], abstract: undefined }];
      render(<ScienceDirectResults {...mockProps} results={resultWithoutAbstract} isExpanded={true} />);
      
      expect(screen.getByText(mockScienceDirectResults[0].title)).toBeInTheDocument();
      // Should not crash and should still render other content
    });

    it('handles four authors correctly', () => {
      const resultWithFourAuthors = [{ 
        ...mockScienceDirectResults[0], 
        authors: ['Author One', 'Author Two', 'Author Three', 'Author Four'] 
      }];
      render(<ScienceDirectResults {...mockProps} results={resultWithFourAuthors} isExpanded={true} />);
      
      expect(screen.getByText('Author One, Author Two, Author Three and Author Four')).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('applies correct CSS classes for visual hierarchy', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      
      const headerButton = screen.getByRole('button');
      expect(headerButton).toHaveClass('hover:bg-gray-50');
      
      const results = screen.getByText(mockScienceDirectResults[0].title).closest('.border-l-4');
      expect(results).toHaveClass('border-l-4', 'border-purple-500');
    });

    it('shows correct chevron rotation based on expansion state', () => {
      const { rerender } = render(<ScienceDirectResults {...mockProps} isExpanded={false} />);
      
      let chevron = screen.getByRole('button').querySelector('svg');
      expect(chevron).not.toHaveClass('rotate-180');
      
      rerender(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      chevron = screen.getByRole('button').querySelector('svg');
      expect(chevron).toHaveClass('rotate-180');
    });

    it('handles flexible layout for metadata', () => {
      render(<ScienceDirectResults {...mockProps} isExpanded={true} />);
      
      // Check that metadata section uses flex-wrap for responsive layout
      const metadataSection = screen.getByText('John Smith et al.').closest('div');
      expect(metadataSection).toHaveClass('flex-wrap');
    });
  });
});