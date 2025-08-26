import api from './api';
import { ResearchQuery, ResearchResult, SubmitResearchRequest, ApiResponse } from './types';

export class ResearchAPI {
  // Submit a new research query
  static async submitQuery(request: SubmitResearchRequest): Promise<ResearchQuery> {
    const response = await api.post<ApiResponse<ResearchQuery>>('/api/research/query', request);
    return response.data.data;
  }

  // Get research results by query ID
  static async getResults(queryId: string): Promise<ResearchResult> {
    const response = await api.get<ApiResponse<ResearchResult>>(`/api/research/results/${queryId}`);
    return response.data.data;
  }

  // Get research status by query ID
  static async getStatus(queryId: string): Promise<{ status: string; progress?: number }> {
    const response = await api.get<ApiResponse<{ status: string; progress?: number }>>(`/api/research/status/${queryId}`);
    return response.data.data;
  }

  // Get user's research history
  static async getHistory(): Promise<ResearchQuery[]> {
    const response = await api.get<ApiResponse<ResearchQuery[]>>('/api/research/history');
    return response.data.data;
  }

  // Health check
  static async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get<ApiResponse<{ status: string; timestamp: string }>>('/api/health');
    return response.data.data;
  }
}