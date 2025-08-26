'use client';

import { useState } from 'react';
import { ResearchResult } from '@/lib/types';
import { LoadingIndicator } from './ui/LoadingIndicator';
import { ScholarResults, BooksResults, ScienceDirectResults } from './results';
import ErrorMessage from './ui/ErrorMessage';

interface ResultsDisplayProps {
  results?: ResearchResult;
  isLoading?: boolean;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

export default function ResultsDisplay({ 
  results, 
  isLoading = false, 
  error,
  onRetry,
  className = '' 
}: ResultsDisplayProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary']));

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const isExpanded = (sectionId: string) => expandedSections.has(sectionId);

  // Loading state
  if (isLoading) {
    return (
      <div className={`w-full max-w-6xl mx-auto ${className}`}>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <LoadingIndicator 
            message="Searching academic sources..." 
            size="lg" 
          />
          <div className="mt-6 space-y-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">
                This may take a few moments as we search multiple databases
              </p>
            </div>
            {/* Progress indicators */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              {[
                { name: 'Google Scholar', icon: '🎓' },
                { name: 'Google Books', icon: '📚' },
                { name: 'ScienceDirect', icon: '🔬' }
              ].map((source) => (
                <div key={source.name} className="flex items-center justify-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-2xl mb-2">{source.icon}</div>
                    <p className="text-sm font-medium text-gray-700">{source.name}</p>
                    <div className="mt-2">
                      <LoadingIndicator size="sm" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`w-full max-w-6xl mx-auto ${className}`}>
        <ErrorMessage
          title="Research Failed"
          message={error}
          onRetry={onRetry}
          variant="card"
          className="max-w-2xl mx-auto"
        />
      </div>
    );
  }

  // No results state
  if (!results) {
    return (
      <div className={`w-full max-w-6xl mx-auto ${className}`}>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Research Results</h3>
          <p className="text-gray-600">Submit a research query to see results here.</p>
        </div>
      </div>
    );
  }

  // Calculate total results count
  const totalResults = Object.values(results.sources).reduce(
    (total, sourceResults) => total + (sourceResults?.length || 0), 
    0
  );

  return (
    <div className={`w-full max-w-6xl mx-auto space-y-6 ${className}`}>
      {/* Results Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Research Results</h2>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {totalResults} results found
            </span>
            {results.cached && (
              <span className="flex items-center text-blue-600">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                </svg>
                Cached results
              </span>
            )}
            <span className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
              {Math.round(results.confidence_score * 100)}% confidence
            </span>
          </div>
        </div>

        {/* AI Summary Section */}
        <div className="border-t pt-4">
          <button
            onClick={() => toggleSection('summary')}
            className="flex items-center justify-between w-full text-left"
            aria-expanded={isExpanded('summary')}
          >
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
              </svg>
              AI Research Summary
            </h3>
            <svg 
              className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded('summary') ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {isExpanded('summary') && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-gray-800 leading-relaxed">{results.summary}</p>
            </div>
          )}
        </div>
      </div>

      {/* Source Results */}
      <div className="space-y-6">
        {/* Google Scholar Results */}
        {results.sources.google_scholar && results.sources.google_scholar.length > 0 && (
          <ScholarResults
            results={results.sources.google_scholar}
            isExpanded={isExpanded('scholar')}
            onToggle={() => toggleSection('scholar')}
          />
        )}

        {/* Google Books Results */}
        {results.sources.google_books && results.sources.google_books.length > 0 && (
          <BooksResults
            results={results.sources.google_books}
            isExpanded={isExpanded('books')}
            onToggle={() => toggleSection('books')}
          />
        )}

        {/* ScienceDirect Results */}
        {results.sources.sciencedirect && results.sources.sciencedirect.length > 0 && (
          <ScienceDirectResults
            results={results.sources.sciencedirect}
            isExpanded={isExpanded('sciencedirect')}
            onToggle={() => toggleSection('sciencedirect')}
          />
        )}
      </div>

      {/* No results message */}
      {totalResults === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <svg className="w-12 h-12 text-yellow-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h3 className="text-lg font-medium text-yellow-800 mb-2">No Results Found</h3>
          <p className="text-yellow-700">
            We couldn&apos;t find any results for your research query. Try refining your search terms or using different keywords.
          </p>
        </div>
      )}
    </div>
  );
}