'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import MainLayout from '@/components/layout/MainLayout';
import Breadcrumb from '@/components/ui/Breadcrumb';
import ResultsDisplay from '@/components/ResultsDisplay';
import LoadingIndicator from '@/components/ui/LoadingIndicator';
import ErrorMessage from '@/components/ui/ErrorMessage';
import { useResearchResults, useResearchStatus } from '@/hooks/useResearch';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { showToast } from '@/components/ui/Toast';

interface ResultsPageProps {
  params: {
    id: string;
  };
}

export default function ResultsPage({ params }: ResultsPageProps) {
  const router = useRouter();
  const queryId = params.id;
  const { handleError } = useErrorHandler();
  
  const { 
    data: results, 
    isLoading: resultsLoading, 
    error: resultsError,
    refetch: refetchResults
  } = useResearchResults(queryId);
  
  const { 
    data: status, 
    isLoading: statusLoading,
    refetch: refetchStatus
  } = useResearchStatus(queryId);

  const breadcrumbItems = [
    { label: 'Research Results', current: true }
  ];

  const isLoading = resultsLoading || statusLoading;
  const isProcessing = status?.status === 'pending' || status?.status === 'processing';
  const hasError = resultsError || status?.status === 'failed';

  const handleRetry = async () => {
    try {
      showToast.loading('Retrying research query...');
      await Promise.all([refetchResults(), refetchStatus()]);
      showToast.dismiss();
      showToast.success('Research data refreshed successfully!');
    } catch (error) {
      showToast.dismiss();
      handleError(error, {
        fallbackMessage: 'Failed to retry research query. Please try again.',
      });
    }
  };

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Breadcrumb */}
          <div className="mb-6">
            <Breadcrumb items={breadcrumbItems} />
          </div>

          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Research Results</h1>
                <p className="text-gray-600 mt-2">
                  Query ID: <code className="bg-gray-100 px-2 py-1 rounded text-sm">{queryId}</code>
                </p>
              </div>
              <div className="flex space-x-4">
                <Link
                  href="/"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  New Research
                </Link>
                <Link
                  href="/history"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  View History
                </Link>
              </div>
            </div>
          </div>

          {/* Status and Progress */}
          {isProcessing && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <LoadingIndicator size="sm" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    Research in Progress
                  </h3>
                  <p className="text-sm text-blue-600 mt-1">
                    {status?.status === 'pending' 
                      ? 'Your research query is queued for processing...'
                      : 'Gathering information from academic sources...'
                    }
                  </p>
                  {status?.progress && (
                    <div className="mt-2">
                      <div className="bg-blue-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${status.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-blue-600 mt-1">{status.progress}% complete</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Error State */}
          {hasError && (
            <div className="mb-6">
              <ErrorMessage
                title="Research Failed"
                message={resultsError?.message || "There was an error processing your research query. Please try again."}
                onRetry={handleRetry}
                variant="banner"
              />
            </div>
          )}

          {/* Results */}
          {results && !isProcessing && !hasError && (
            <ResultsDisplay 
              results={results} 
              onRetry={handleRetry}
            />
          )}

          {/* Loading State */}
          {isLoading && !isProcessing && (
            <div className="flex justify-center items-center py-12">
              <LoadingIndicator />
              <span className="ml-3 text-gray-600">Loading research results...</span>
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}