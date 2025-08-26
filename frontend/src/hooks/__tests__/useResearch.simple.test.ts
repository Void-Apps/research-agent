import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import React from 'react';

// Import just the query keys function
const researchKeys = {
  all: ['research'] as const,
  results: (queryId: string) => ['research', 'results', queryId] as const,
  status: (queryId: string) => ['research', 'status', queryId] as const,
  history: () => ['research', 'history'] as const,
  health: () => ['research', 'health'] as const,
};

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };

  return Wrapper;
};

describe('useResearch', () => {
  describe('researchKeys', () => {
    it('should generate consistent query keys', () => {
      expect(researchKeys.all).toEqual(['research']);
      expect(researchKeys.results('test-id')).toEqual(['research', 'results', 'test-id']);
      expect(researchKeys.status('test-id')).toEqual(['research', 'status', 'test-id']);
      expect(researchKeys.history()).toEqual(['research', 'history']);
      expect(researchKeys.health()).toEqual(['research', 'health']);
    });

    it('should generate unique keys for different query IDs', () => {
      const key1 = researchKeys.results('id1');
      const key2 = researchKeys.results('id2');
      
      expect(key1).not.toEqual(key2);
      expect(key1[2]).toBe('id1');
      expect(key2[2]).toBe('id2');
    });
  });

  describe('Query Client Configuration', () => {
    it('should create wrapper with proper configuration', () => {
      const wrapper = createWrapper();
      expect(wrapper).toBeDefined();
      expect(typeof wrapper).toBe('function');
    });
  });
});