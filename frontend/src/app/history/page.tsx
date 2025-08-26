'use client';

import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import MainLayout from '@/components/layout/MainLayout';
import Breadcrumb from '@/components/ui/Breadcrumb';
import LoadingIndicator from '@/components/ui/LoadingIndicator';
import { useResearchHistory } from '@/hooks/useResearch';
import { QueryStatus } from '@/lib/types';

const getStatusColor = (status: QueryStatus) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'processing':
      return 'bg-blue-100 text-blue-800';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getStatusText = (status: QueryStatus) => {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'processing':
      return 'Processing';
    case 'pending':
      return 'Pending';
    case 'failed':
      return 'Failed';
    default:
      return 'Unknown';
  }
};

export default function HistoryPage() {
  const { data: history, isLoading, error } = useResearchHistory();

  const breadcrumbItems = [
    { label: 'Research History', current: true }
  ];

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
                <h1 className="text-3xl font-bold text-gray-900">Research History</h1>
                <p className="text-gray-600 mt-2">
                  View and manage your previous research queries
                </p>
              </div>
              <Link
                href="/"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                New Research
              </Link>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex justify-center items-center py-12">
              <LoadingIndicator />
              <span className="ml-3 text-gray-600">Loading research history...</span>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Failed to Load History
                  </h3>
                  <p className="text-sm text-red-600 mt-1">
                    There was an error loading your research history. Please try again.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {history && history.length === 0 && (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No research history</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by submitting your first research query.
              </p>
              <div className="mt-6">
                <Link
                  href="/"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Start Research
                </Link>
              </div>
            </div>
          )}

          {/* History List */}
          {history && history.length > 0 && (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {history.map((query) => (
                  <li key={query.id}>
                    <Link
                      href={`/results/${query.id}`}
                      className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {query.query}
                          </p>
                          <p className="text-sm text-gray-500 mt-1">
                            {formatDistanceToNow(new Date(query.timestamp), { addSuffix: true })}
                          </p>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                              query.status
                            )}`}
                          >
                            {getStatusText(query.status)}
                          </span>
                          <div className="flex-shrink-0">
                            <svg
                              className="h-5 w-5 text-gray-400"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 5l7 7-7 7"
                              />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}