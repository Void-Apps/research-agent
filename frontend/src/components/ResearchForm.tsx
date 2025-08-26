'use client';

import { useState, FormEvent } from 'react';
import { useSubmitResearch } from '@/hooks/useResearch';
import { LoadingIndicator } from './ui/LoadingIndicator';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { showToast } from '@/components/ui/Toast';
import ErrorMessage from '@/components/ui/ErrorMessage';

interface ResearchFormProps {
  onSubmit?: (queryId: string) => void;
  className?: string;
}

export default function ResearchForm({ onSubmit, className = '' }: ResearchFormProps) {
  const [query, setQuery] = useState('');
  const [errors, setErrors] = useState<{ query?: string }>({});
  
  const submitResearch = useSubmitResearch();
  const { handleError } = useErrorHandler();

  const validateForm = (): boolean => {
    const newErrors: { query?: string } = {};
    
    if (!query.trim()) {
      newErrors.query = 'Research query is required';
    } else if (query.trim().length < 3) {
      newErrors.query = 'Research query must be at least 3 characters long';
    } else if (query.trim().length > 500) {
      newErrors.query = 'Research query must be less than 500 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      const result = await submitResearch.mutateAsync({
        query: query.trim(),
      });
      
      // Clear form on success
      setQuery('');
      setErrors({});
      
      // Show success toast
      showToast.success('Research started successfully!');
      
      // Call onSubmit callback with the query ID
      onSubmit?.(result.id);
    } catch (error) {
      // Use our error handler for consistent error handling
      handleError(error, {
        fallbackMessage: 'Failed to submit research query. Please try again.',
      });
    }
  };

  const handleInputChange = (value: string) => {
    setQuery(value);
    // Clear errors when user starts typing
    if (errors.query) {
      setErrors({ ...errors, query: undefined });
    }
  };

  const isLoading = submitResearch.isPending;
  const hasError = submitResearch.isError;
  const errorMessage = submitResearch.error?.message || 'Failed to submit research query';

  return (
    <div className={`w-full max-w-4xl mx-auto ${className}`}>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label 
            htmlFor="research-query" 
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Research Query
          </label>
          <div className="relative">
            <textarea
              id="research-query"
              name="query"
              rows={4}
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              placeholder="Enter your research topic or question here... (e.g., 'machine learning applications in healthcare', 'climate change impact on agriculture')"
              className={`
                block w-full px-3 py-2 border rounded-md shadow-sm 
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
                resize-none
                ${errors.query ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'}
              `}
              disabled={isLoading}
              aria-describedby={errors.query ? 'query-error' : undefined}
              aria-invalid={!!errors.query}
            />
            {isLoading && (
              <div className="absolute right-3 top-3">
                <LoadingIndicator size="sm" />
              </div>
            )}
          </div>
          
          {/* Character count */}
          <div className="flex justify-between items-center mt-1">
            <div>
              {errors.query && (
                <p id="query-error" className="text-sm text-red-600" role="alert">
                  {errors.query}
                </p>
              )}
            </div>
            <p className={`text-xs ${query.length > 450 ? 'text-red-500' : 'text-gray-500'}`}>
              {query.length}/500
            </p>
          </div>
        </div>

        {/* Global error message */}
        {hasError && (
          <ErrorMessage
            title="Research Submission Failed"
            message={errorMessage}
            onRetry={() => handleSubmit({ preventDefault: () => {} } as FormEvent<HTMLFormElement>)}
            variant="inline"
          />
        )}

        {/* Submit button */}
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={isLoading}
            className={`
              inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors duration-200
              ${isLoading 
                ? 'bg-blue-400 cursor-not-allowed' 
                : !query.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
              }
            `}
          >
            {isLoading ? (
              <>
                <LoadingIndicator size="sm" className="mr-2" />
                Processing Research...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Start Research
              </>
            )}
          </button>
        </div>
      </form>

      {/* Help text */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600">
          Our AI will search Google Scholar, Google Books, and ScienceDirect to provide comprehensive research findings.
        </p>
      </div>
    </div>
  );
}