'use client';

import { SourceResult } from '@/lib/types';

interface BooksResultsProps {
  results: SourceResult[];
  isExpanded: boolean;
  onToggle: () => void;
}

export default function BooksResults({ results, isExpanded, onToggle }: BooksResultsProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Date not available';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return dateString;
      }
      return date.getFullYear().toString();
    } catch {
      return dateString;
    }
  };

  const formatAuthors = (authors: string[]) => {
    if (!authors || authors.length === 0) return 'Authors not available';
    if (authors.length === 1) return authors[0];
    if (authors.length === 2) return authors.join(' and ');
    if (authors.length <= 3) return authors.slice(0, -1).join(', ') + ' and ' + authors[authors.length - 1];
    return `${authors[0]} et al.`;
  };

  const truncateText = (text: string, maxLength: number = 350) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  const formatISBN = (isbn?: string) => {
    if (!isbn) return null;
    // Format ISBN with dashes for readability
    if (isbn.length === 13) {
      // ISBN-13 format: 978-X-XX-XXXXXX-X
      return `${isbn.slice(0, 3)}-${isbn.slice(3, 4)}-${isbn.slice(4, 6)}-${isbn.slice(6, 12)}-${isbn.slice(12)}`;
    }
    if (isbn.length === 10) {
      // ISBN-10 format: X-XXX-XXXXX-X
      return `${isbn.slice(0, 1)}-${isbn.slice(1, 4)}-${isbn.slice(4, 9)}-${isbn.slice(9)}`;
    }
    return isbn;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full p-6 text-left hover:bg-gray-50 transition-colors"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center">
          <div className="flex-shrink-0 w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
            <span className="text-2xl">📚</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Google Books</h3>
            <p className="text-sm text-gray-600">
              {results.length} {results.length === 1 ? 'book' : 'books'} found
            </p>
          </div>
        </div>
        <div className="flex items-center">
          <span className="text-sm text-gray-500 mr-2">
            {isExpanded ? 'Hide' : 'Show'} results
          </span>
          <svg 
            className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200">
          <div className="p-6 space-y-6">
            {results.map((result, index) => (
              <div key={index} className="border-l-4 border-green-500 pl-4 py-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-lg font-medium text-gray-900 mb-2 leading-tight">
                      {result.url ? (
                        <a 
                          href={result.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-800 hover:underline"
                        >
                          {result.title}
                        </a>
                      ) : (
                        result.title
                      )}
                    </h4>
                    
                    <div className="flex items-center text-sm text-gray-600 mb-3 space-x-4">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                        {formatAuthors(result.authors)}
                      </span>
                      
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                        </svg>
                        {formatDate(result.publication_date)}
                      </span>
                      
                      {result.isbn && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                            <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                          </svg>
                          ISBN: {formatISBN(result.isbn)}
                        </span>
                      )}
                    </div>

                    {result.abstract && (
                      <div className="mb-3">
                        <p className="text-gray-700 leading-relaxed">
                          {truncateText(result.abstract)}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Book
                        </span>
                        {result.preview_link && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Preview Available
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        {result.preview_link && (
                          <a 
                            href={result.preview_link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
                          >
                            <span>Preview</span>
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </a>
                        )}
                        
                        {result.url && (
                          <a 
                            href={result.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-green-600 hover:text-green-800"
                          >
                            <span>View Book</span>
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}