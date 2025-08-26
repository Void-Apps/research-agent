/**
 * Mock data fixtures for testing
 */

export const mockResearchQuery = {
  id: 'test-query-123',
  query: 'artificial intelligence machine learning',
  user_id: 'test-user',
  timestamp: '2024-01-15T10:30:00Z',
  status: 'completed' as const,
}

export const mockScholarResult = {
  title: 'Deep Learning for Natural Language Processing',
  authors: ['John Smith', 'Jane Doe'],
  abstract: 'This paper presents a comprehensive study of deep learning techniques for NLP tasks.',
  citation_count: 150,
  url: 'https://scholar.google.com/citations?view_op=view_citation&hl=en&user=test',
  publication_year: 2023,
}

export const mockBooksResult = {
  title: 'Machine Learning: A Comprehensive Guide',
  authors: ['Alice Johnson'],
  description: 'A complete guide to machine learning algorithms and applications.',
  isbn: '978-0123456789',
  preview_link: 'https://books.google.com/books?id=test',
  published_date: '2023-01-01',
}

export const mockScienceDirectResult = {
  title: 'Advanced Neural Networks in Computer Vision',
  authors: ['Bob Wilson', 'Carol Brown'],
  abstract: 'This study explores the application of neural networks in computer vision tasks.',
  doi: '10.1016/j.test.2023.01.001',
  journal: 'Journal of Artificial Intelligence',
  publication_date: '2023-02-15T00:00:00Z',
}

export const mockResearchResult = {
  query_id: 'test-query-123',
  sources: {
    google_scholar: [mockScholarResult],
    google_books: [mockBooksResult],
    sciencedirect: [mockScienceDirectResult],
  },
  ai_summary: 'The research shows significant advances in AI and machine learning applications.',
  confidence_score: 0.85,
  cached: false,
}

export const mockResearchHistory = [
  {
    id: 'query-1',
    query: 'machine learning algorithms',
    timestamp: '2024-01-15T10:30:00Z',
    status: 'completed',
  },
  {
    id: 'query-2',
    query: 'deep learning neural networks',
    timestamp: '2024-01-14T15:45:00Z',
    status: 'completed',
  },
  {
    id: 'query-3',
    query: 'natural language processing',
    timestamp: '2024-01-13T09:20:00Z',
    status: 'failed',
  },
]

export const mockApiError = {
  error: 'ValidationError',
  message: 'Invalid query parameter',
  details: { field: 'query', issue: 'Query cannot be empty' },
  timestamp: '2024-01-15T10:30:00Z',
  request_id: 'req-123',
}

export const mockLoadingStates = {
  isLoading: false,
  isError: false,
  error: null,
  data: null,
}

// Mock API responses
export const mockApiResponses = {
  research: {
    success: {
      status: 200,
      data: mockResearchResult,
    },
    error: {
      status: 400,
      data: mockApiError,
    },
    loading: {
      status: 202,
      data: { message: 'Research in progress', query_id: 'test-query-123' },
    },
  },
  history: {
    success: {
      status: 200,
      data: mockResearchHistory,
    },
    empty: {
      status: 200,
      data: [],
    },
  },
}

// Test utilities
export const createMockFetch = (response: any, status = 200) => {
  return jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(response),
    text: jest.fn().mockResolvedValue(JSON.stringify(response)),
  })
}

export const createMockFetchError = (error: Error) => {
  return jest.fn().mockRejectedValue(error)
}