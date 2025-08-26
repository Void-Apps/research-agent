import { queryClient } from '../query-client';

describe('Query Client Configuration', () => {
  it('should have proper default options configured', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    
    // Check queries configuration
    expect(defaultOptions.queries?.staleTime).toBe(5 * 60 * 1000); // 5 minutes
    expect(defaultOptions.queries?.gcTime).toBe(10 * 60 * 1000); // 10 minutes
    expect(defaultOptions.queries?.refetchOnWindowFocus).toBe(false);
    expect(defaultOptions.queries?.refetchOnReconnect).toBe(true);
    expect(defaultOptions.queries?.refetchIntervalInBackground).toBe(false);
    
    // Check mutations configuration
    expect(typeof defaultOptions.mutations?.retry).toBe('function');
    expect(defaultOptions.mutations?.retryDelay).toBe(1000);
  });

  it('should have proper retry logic for queries', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    const retryFn = defaultOptions.queries?.retry as Function;
    
    // Should not retry on 4xx errors
    expect(retryFn(1, { response: { status: 404 } })).toBe(false);
    expect(retryFn(1, { response: { status: 403 } })).toBe(false);
    expect(retryFn(1, { response: { status: 400 } })).toBe(false);
    
    // Should retry on 5xx errors up to 3 times
    expect(retryFn(1, { response: { status: 500 } })).toBe(true);
    expect(retryFn(2, { response: { status: 500 } })).toBe(true);
    expect(retryFn(3, { response: { status: 500 } })).toBe(false);
    
    // Should retry on network errors
    expect(retryFn(1, new Error('Network error'))).toBe(true);
    expect(retryFn(2, new Error('Network error'))).toBe(true);
    expect(retryFn(3, new Error('Network error'))).toBe(false);
  });

  it('should have proper retry logic for mutations', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    const retryFn = defaultOptions.mutations?.retry as Function;
    
    // Should not retry on 4xx errors
    expect(retryFn(1, { response: { status: 404 } })).toBe(false);
    expect(retryFn(1, { response: { status: 403 } })).toBe(false);
    expect(retryFn(1, { response: { status: 400 } })).toBe(false);
    
    // Should retry on 5xx errors up to 2 times
    expect(retryFn(1, { response: { status: 500 } })).toBe(true);
    expect(retryFn(2, { response: { status: 500 } })).toBe(false);
    
    // Should retry on network errors
    expect(retryFn(1, new Error('Network error'))).toBe(true);
    expect(retryFn(2, new Error('Network error'))).toBe(false);
  });

  it('should have exponential backoff retry delay', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    const retryDelayFn = defaultOptions.queries?.retryDelay as Function;
    
    // Test exponential backoff with max cap
    expect(retryDelayFn(0)).toBe(1000); // 2^0 * 1000 = 1000
    expect(retryDelayFn(1)).toBe(2000); // 2^1 * 1000 = 2000
    expect(retryDelayFn(2)).toBe(4000); // 2^2 * 1000 = 4000
    expect(retryDelayFn(3)).toBe(8000); // 2^3 * 1000 = 8000
    expect(retryDelayFn(10)).toBe(30000); // Should cap at 30000
  });

  it('should be properly initialized', () => {
    expect(queryClient).toBeDefined();
    expect(queryClient.getQueryCache()).toBeDefined();
    expect(queryClient.getMutationCache()).toBeDefined();
  });
});