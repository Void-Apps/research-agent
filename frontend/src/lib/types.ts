// API Response Types
export interface ResearchQuery {
  id: string;
  query: string;
  user_id?: string;
  timestamp: string;
  status: QueryStatus;
}

export interface ResearchResult {
  query_id: string;
  sources: {
    google_scholar?: SourceResult[];
    google_books?: SourceResult[];
    sciencedirect?: SourceResult[];
  };
  summary: string;
  confidence_score: number;
  cached: boolean;
}

export interface SourceResult {
  title: string;
  authors: string[];
  abstract?: string;
  url?: string;
  publication_date?: string;
  source_type: SourceType;
  // Source-specific fields
  citation_count?: number; // Google Scholar
  isbn?: string; // Google Books
  preview_link?: string; // Google Books
  doi?: string; // ScienceDirect
  journal?: string; // ScienceDirect
}

export type QueryStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type SourceType = 'google_scholar' | 'google_books' | 'sciencedirect';

// API Request Types
export interface SubmitResearchRequest {
  query: string;
  user_id?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
  request_id: string;
}

// Component Props Types
export interface ResearchFormProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
}

export interface ResultsDisplayProps {
  results: ResearchResult;
  isLoading?: boolean;
}