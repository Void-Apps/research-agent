'use client';

import { SourceResult } from '@/lib/types';

interface ScienceDirectResultsProps {
  results: SourceResult[];
  isExpanded: boolean;
  onToggle: () => void;
}

export default function ScienceDirectResults({ results, isExpanded, onToggle }: ScienceDirectResultsProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Date not available';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return dateString;
      }
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateString;
    }
  };

  const formatAuthors = (authors: string[]) => {
    if (!authors || authors.length === 0) return 'Authors not available';
    if (authors.length === 1) return authors[0];
    if (authors.length === 2) return authors.join(' and ');
    if (authors.length <= 4) return authors.slice(0, -1).join(', ') + ' and ' + authors[authors.length - 1];
    return `${authors[0]} et al.`;
  };

  const truncateText = (text: string, maxLength: number = 400) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  const formatDOI = (doi?: string) => {
    if (!doi) return null;
    // Remove common DOI prefixes if present
    const cleanDOI = doi.replace(/^(https?:\/\/)?(dx\.)?doi\.org\//, '');
    return cleanDOI;
  };

  const getDOIUrl = (doi?: string) => {
    if (!doi) return null;
    const cleanDOI = formatDOI(doi);
    return `https://doi.org/${cleanDOI}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full p-6 text-left hover:bg-gray-50 transition-colors"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center">
          <div className="flex-shrink-0 w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
            <span className="text-2xl">🔬</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">ScienceDirect</h3>
            <p className="text-sm text-gray-600">
              {results.length} scientific {results.length === 1 ? 'paper' : 'papers'} found
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
              <div key={index} className="border-l-4 border-purple-500 pl-4 py-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-lg font-medium text-gray-900 mb-2 leading-tight">
                      {result.url ? (
                        <a 
                          href={result.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-purple-600 hover:text-purple-800 hover:underline"
                        >
                          {result.title}
                        </a>
                      ) : (
                        result.title
                      )}
                    </h4>
                    
                    <div className="flex flex-wrap items-center text-sm text-gray-600 mb-3 gap-x-4 gap-y-1">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                        {formatAuthors(result.authors)}
                      </span>
                      
                      {result.journal && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                            <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm7 5a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
                          </svg>
                          {result.journal}
                        </span>
                      )}
                      
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                        </svg>
                        {formatDate(result.publication_date)}
                      </span>
                      
                      {result.doi && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                          </svg>
                          DOI: {formatDOI(result.doi)}
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
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          Scientific Paper
                        </span>
                        {result.journal && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Peer Reviewed
                          </span>
                        )}
                        {result.doi && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            DOI Available
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        {result.doi && (
                          <a 
                            href={getDOIUrl(result.doi) || '#'} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
                          >
                            <span>DOI Link</span>
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                            </svg>
                          </a>
                        )}
                        
                        {result.url && (
                          <a 
                            href={result.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-purple-600 hover:text-purple-800"
                          >
                            <span>View Paper</span>
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