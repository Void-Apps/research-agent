import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import BooksResults from '../results/BooksResults';
import { SourceResult } from '@/lib/types';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

const mockBooksResults: SourceResult[] = [
  {
    title: 'Artificial Intelligence: A Modern Approach',
    authors: ['Stuart Russell', 'Peter Norvig'],
    abstract: 'This comprehensive textbook covers the fundamentals of artificial intelligence, including machine learning, natural language processing, and robotics. It provides both theoretical foundations and practical applications.',
    url: 'https://books.google.com/book1',
    publication_date: '2020-04-28',
    source_type: 'google_books',
    isbn: '9780134610993',
    preview_link: 'https://books.google.com/preview/book1',
  },
  {
    title: 'Deep Learning',
    authors: ['Ian Goodfellow', 'Yoshua Bengio', 'Aaron Courville'],
    abstract: 'An introduction to deep learning covering mathematical and conceptual background, deep networks for modern applications, and research perspectives.',
    url: 'https://books.google.com/book2',
    publication_date: '2016-11-18',
    source_type: 'google_books',
    isbn: '9780262035613',
  },
  {
    title: 'Pattern Recognition and Machine Learning',
    authors: ['Christopher Bishop'],
    abstract: 'A comprehensive introduction to the fields of pattern recognition and machine learning.',
    publication_date: '2006-08-17',
    source_type: 'google_books',
    preview_link: 'https://books.google.com/preview/book3',
  },
];

const mockProps = {
  results: mockBooksResults,
  isExpanded: false,
  onToggle: jest.fn(),
};

describe('BooksResults', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Header Section', () => {
    it('renders header with correct title and count', () => {
      render(<BooksResults {...mockProps} />);
      
      expect(screen.getByText('Google Books')).toBeInTheDocument();
      expect(screen.getByText('3 books found')).toBeInTheDocument();
      expect(screen.getByText('📚')).toBeInTheDocument();
    });

    it('shows singular form when only one result', () => {
      render(<BooksResults {...mockProps} results={[mockBooksResults[0]]} />);
      
      expect(screen.getByText('1 book found')).toBeInTheDocument();
    });

    it('calls onToggle when header is clicked', () => {
      render(<BooksResults {...mockProps} />);
      
      const headerButton = screen.getByRole('button');
      fireEvent.click(headerButton);
      
      expect(mockProps.onToggle).toHaveBeenCalledTimes(1);
    });

    it('shows correct expand/collapse text', () => {
      const { rerender } = render(<BooksResults {...mockProps} isExpanded={false} />);
      expect(screen.getByText('Show results')).toBeInTheDocument();
      
      rerender(<BooksResults {...mockProps} isExpanded={true} />);
      expect(screen.getByText('Hide results')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<BooksResults {...mockProps} isExpanded={true} />);
      
      const headerButton = screen.getByRole('button');
      expect(headerButton).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Collapsed State', () => {
    it('does not show results when collapsed', () => {
      render(<BooksResults {...mockProps} isExpanded={false} />);
      
      expect(screen.queryByText(mockBooksResults[0].title)).not.toBeInTheDocument();
      expect(screen.queryByText(mockBooksResults[0].abstract!)).not.toBeInTheDocument();
    });
  });

  describe('Expanded State', () => {
    const expandedProps = { ...mockProps, isExpanded: true };

    it('shows all results when expanded', () => {
      render(<BooksResults {...expandedProps} />);
      
      mockBooksResults.forEach(result => {
        expect(screen.getByText(result.title)).toBeInTheDocument();
      });
    });

    it('renders book titles as clickable links when URL is provided', () => {
      render(<BooksResults {...expandedProps} />);
      
      const titleLink = screen.getByRole('link', { name: mockBooksResults[0].title });
      expect(titleLink).toHaveAttribute('href', mockBooksResults[0].url);
      expect(titleLink).toHaveAttribute('target', '_blank');
      expect(titleLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders book titles as plain text when no URL', () => {
      const resultsWithoutUrl = [{ ...mockBooksResults[2] }]; // Third book has no URL
      render(<BooksResults {...expandedProps} results={resultsWithoutUrl} />);
      
      expect(screen.getByText(mockBooksResults[2].title)).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: mockBooksResults[2].title })).not.toBeInTheDocument();
    });

    it('formats authors correctly', () => {
      render(<BooksResults {...expandedProps} />);
      
      // Two authors should show "Author1 and Author2"
      expect(screen.getByText('Stuart Russell and Peter Norvig')).toBeInTheDocument();
      
      // Three authors should show "Author1, Author2 and Author3"
      expect(screen.getByText('Ian Goodfellow, Yoshua Bengio and Aaron Courville')).toBeInTheDocument();
      
      // Single author should show full name
      expect(screen.getByText('Christopher Bishop')).toBeInTheDocument();
    });

    it('formats publication dates correctly', () => {
      render(<BooksResults {...expandedProps} />);
      
      expect(screen.getByText('2020')).toBeInTheDocument();
      expect(screen.getByText('2016')).toBeInTheDocument();
      expect(screen.getByText('2006')).toBeInTheDocument();
    });

    it('displays ISBN when available', () => {
      render(<BooksResults {...expandedProps} />);
      
      // First verify all books are rendered
      expect(screen.getByText('Artificial Intelligence: A Modern Approach')).toBeInTheDocument();
      expect(screen.getByText('Deep Learning')).toBeInTheDocument();
      expect(screen.getByText('Pattern Recognition and Machine Learning')).toBeInTheDocument();
      
      // Then check ISBNs
      expect(screen.getByText('ISBN: 978-0-13-461099-3')).toBeInTheDocument();
      expect(screen.getByText('ISBN: 978-0-26-203561-3')).toBeInTheDocument();
    });

    it('shows abstracts when available', () => {
      render(<BooksResults {...expandedProps} />);
      
      mockBooksResults.forEach(result => {
        if (result.abstract) {
          expect(screen.getByText(result.abstract, { exact: false })).toBeInTheDocument();
        }
      });
    });

    it('truncates long abstracts', () => {
      const longAbstract = 'A'.repeat(400);
      const resultWithLongAbstract = [{ ...mockBooksResults[0], abstract: longAbstract }];
      
      render(<BooksResults {...expandedProps} results={resultWithLongAbstract} />);
      
      expect(screen.getByText(/A+\.\.\./)).toBeInTheDocument();
    });

    it('shows appropriate badges', () => {
      render(<BooksResults {...expandedProps} />);
      
      expect(screen.getAllByText('Book')).toHaveLength(3);
      expect(screen.getAllByText('Preview Available')).toHaveLength(2); // First and third books have previews
    });

    it('renders Preview links when available', () => {
      render(<BooksResults {...expandedProps} />);
      
      const previewLinks = screen.getAllByText('Preview');
      expect(previewLinks).toHaveLength(2);
      
      expect(previewLinks[0].closest('a')).toHaveAttribute('href', mockBooksResults[0].preview_link);
      expect(previewLinks[1].closest('a')).toHaveAttribute('href', mockBooksResults[2].preview_link);
    });

    it('renders View Book links when URL is available', () => {
      render(<BooksResults {...expandedProps} />);
      
      const viewBookLinks = screen.getAllByText('View Book');
      expect(viewBookLinks).toHaveLength(2); // Only first two books have URLs
      
      expect(viewBookLinks[0].closest('a')).toHaveAttribute('href', mockBooksResults[0].url);
      expect(viewBookLinks[1].closest('a')).toHaveAttribute('href', mockBooksResults[1].url);
    });
  });

  describe('ISBN Formatting', () => {
    it('formats 13-digit ISBN correctly', () => {
      render(<BooksResults {...mockProps} isExpanded={true} />);
      
      expect(screen.getByText('ISBN: 978-0-13-461099-3')).toBeInTheDocument();
    });

    it('formats 10-digit ISBN correctly', () => {
      const resultWith10DigitISBN = [{ 
        ...mockBooksResults[0], 
        isbn: '0134610997' 
      }];
      
      render(<BooksResults {...mockProps} results={resultWith10DigitISBN} isExpanded={true} />);
      
      expect(screen.getByText('ISBN: 0-134-61099-7')).toBeInTheDocument();
    });

    it('handles malformed ISBN gracefully', () => {
      const resultWithMalformedISBN = [{ 
        ...mockBooksResults[0], 
        isbn: '123-invalid' 
      }];
      
      render(<BooksResults {...mockProps} results={resultWithMalformedISBN} isExpanded={true} />);
      
      expect(screen.getByText('ISBN: 123-invalid')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty results array', () => {
      render(<BooksResults {...mockProps} results={[]} />);
      
      expect(screen.getByText('0 books found')).toBeInTheDocument();
    });

    it('handles missing authors', () => {
      const resultWithoutAuthors = [{ ...mockBooksResults[0], authors: [] }];
      render(<BooksResults {...mockProps} results={resultWithoutAuthors} isExpanded={true} />);
      
      expect(screen.getByText('Authors not available')).toBeInTheDocument();
    });

    it('handles missing publication date', () => {
      const resultWithoutDate = [{ ...mockBooksResults[0], publication_date: undefined }];
      render(<BooksResults {...mockProps} results={resultWithoutDate} isExpanded={true} />);
      
      expect(screen.getByText('Date not available')).toBeInTheDocument();
    });

    it('handles invalid publication date', () => {
      const resultWithInvalidDate = [{ ...mockBooksResults[0], publication_date: 'invalid-date' }];
      render(<BooksResults {...mockProps} results={resultWithInvalidDate} isExpanded={true} />);
      
      expect(screen.getByText('invalid-date')).toBeInTheDocument();
    });

    it('handles missing ISBN', () => {
      const resultWithoutISBN = [{ ...mockBooksResults[0], isbn: undefined }];
      render(<BooksResults {...mockProps} results={resultWithoutISBN} isExpanded={true} />);
      
      expect(screen.queryByText(/ISBN:/)).not.toBeInTheDocument();
    });

    it('handles missing abstract', () => {
      const resultWithoutAbstract = [{ ...mockBooksResults[0], abstract: undefined }];
      render(<BooksResults {...mockProps} results={resultWithoutAbstract} isExpanded={true} />);
      
      expect(screen.getByText(mockBooksResults[0].title)).toBeInTheDocument();
      // Should not crash and should still render other content
    });

    it('handles missing preview link', () => {
      const resultWithoutPreview = [{ ...mockBooksResults[1] }]; // Second book has no preview
      render(<BooksResults {...mockProps} results={resultWithoutPreview} isExpanded={true} />);
      
      expect(screen.getByText('Book')).toBeInTheDocument();
      expect(screen.queryByText('Preview Available')).not.toBeInTheDocument();
      expect(screen.queryByText('Preview')).not.toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('applies correct CSS classes for visual hierarchy', () => {
      render(<BooksResults {...mockProps} isExpanded={true} />);
      
      const headerButton = screen.getByRole('button');
      expect(headerButton).toHaveClass('hover:bg-gray-50');
      
      const results = screen.getByText(mockBooksResults[0].title).closest('.border-l-4');
      expect(results).toHaveClass('border-l-4', 'border-green-500');
    });

    it('shows correct chevron rotation based on expansion state', () => {
      const { rerender } = render(<BooksResults {...mockProps} isExpanded={false} />);
      
      let chevron = screen.getByRole('button').querySelector('svg');
      expect(chevron).not.toHaveClass('rotate-180');
      
      rerender(<BooksResults {...mockProps} isExpanded={true} />);
      chevron = screen.getByRole('button').querySelector('svg');
      expect(chevron).toHaveClass('rotate-180');
    });
  });
});