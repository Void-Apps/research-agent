import { renderHook } from '@testing-library/react';
import { useErrorHandler } from '../useErrorHandler';

// Mock dependencies
jest.mock('../../components/ui/Toast', () => ({
  showToast: {
    error: jest.fn(),
  },
}));

jest.mock('../useOnlineStatus', () => ({
  useOnlineStatus: jest.fn(),
}));

describe('useErrorHandler', () => {
  const mockShowToast = require('../../components/ui/Toast').showToast;
  const mockUseOnlineStatus = require('../useOnlineStatus').useOnlineStatus;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseOnlineStatus.mockReturnValue({ isOnline: true });
  });

  describe('handleError', () => {
    it('should handle HTTP error responses', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = {
        response: {
          status: 404,
          data: { message: 'Not found' },
        },
      };
      
      const apiError = result.current.handleError(error);
      
      expect(apiError).toEqual({
        message: 'Not found',
        status: 404,
        code: undefined,
      });
      expect(mockShowToast.error).toHaveBeenCalledWith('Not found');
    });

    it('should handle HTTP errors with error field in data', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = {
        response: {
          status: 400,
          data: { error: 'Bad request' },
        },
      };
      
      const apiError = result.current.handleError(error);
      
      expect(apiError).toEqual({
        message: 'Bad request',
        status: 400,
        code: undefined,
      });
    });

    it('should use status message when no data message is available', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };
      
      const apiError = result.current.handleError(error);
      
      expect(apiError.message).toBe('Server error. Please try again later.');
      expect(apiError.status).toBe(500);
    });

    it('should handle network errors when online', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = {
        request: {},
      };
      
      const apiError = result.current.handleError(error);
      
      expect(apiError).toEqual({
        message: 'Unable to connect to the server. Please try again.',
        status: 0,
        code: 'NETWORK_ERROR',
      });
    });

    it('should handle network errors when offline', () => {
      mockUseOnlineStatus.mockReturnValue({ isOnline: false });
      const { result } = renderHook(() => useErrorHandler());
      
      const error = {
        request: {},
      };
      
      const apiError = result.current.handleError(error);
      
      expect(apiError).toEqual({
        message: 'You appear to be offline. Please check your connection.',
        status: 0,
        code: 'NETWORK_ERROR',
      });
    });

    it('should handle JavaScript errors', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = new Error('JavaScript error');
      
      const apiError = result.current.handleError(error);
      
      expect(apiError).toEqual({
        message: 'JavaScript error',
        code: 'CLIENT_ERROR',
      });
    });

    it('should handle unknown errors', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = 'Unknown error';
      
      const apiError = result.current.handleError(error);
      
      expect(apiError).toEqual({
        message: 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
      });
    });

    it('should not show toast when showToast is false', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = new Error('Test error');
      
      result.current.handleError(error, { showToast: false });
      
      expect(mockShowToast.error).not.toHaveBeenCalled();
    });

    it('should use custom fallback message', () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = 'Unknown error';
      
      const apiError = result.current.handleError(error, {
        fallbackMessage: 'Custom fallback message',
      });
      
      expect(apiError.message).toBe('Custom fallback message');
    });

    it('should call custom onError callback', () => {
      const { result } = renderHook(() => useErrorHandler());
      const mockOnError = jest.fn();
      
      const error = new Error('Test error');
      
      result.current.handleError(error, { onError: mockOnError });
      
      expect(mockOnError).toHaveBeenCalledWith({
        message: 'Test error',
        code: 'CLIENT_ERROR',
      });
    });

    it('should log errors for debugging', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      const { result } = renderHook(() => useErrorHandler());
      
      const error = new Error('Test error');
      
      result.current.handleError(error);
      
      expect(consoleSpy).toHaveBeenCalledWith('Error handled:', {
        originalError: error,
        apiError: {
          message: 'Test error',
          code: 'CLIENT_ERROR',
        },
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('handleAsyncError', () => {
    it('should return result when async function succeeds', async () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const asyncFn = jest.fn().mockResolvedValue('success');
      
      const response = await result.current.handleAsyncError(asyncFn);
      
      expect(response).toBe('success');
      expect(asyncFn).toHaveBeenCalled();
    });

    it('should handle errors and return null when async function fails', async () => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = new Error('Async error');
      const asyncFn = jest.fn().mockRejectedValue(error);
      
      const response = await result.current.handleAsyncError(asyncFn);
      
      expect(response).toBeNull();
      expect(mockShowToast.error).toHaveBeenCalledWith('Async error');
    });

    it('should pass options to handleError', async () => {
      const { result } = renderHook(() => useErrorHandler());
      const mockOnError = jest.fn();
      
      const error = new Error('Async error');
      const asyncFn = jest.fn().mockRejectedValue(error);
      
      await result.current.handleAsyncError(asyncFn, {
        showToast: false,
        onError: mockOnError,
      });
      
      expect(mockShowToast.error).not.toHaveBeenCalled();
      expect(mockOnError).toHaveBeenCalled();
    });
  });

  describe('status message mapping', () => {
    const statusMessages = [
      [400, 'Invalid request. Please check your input and try again.'],
      [401, 'Authentication required. Please log in and try again.'],
      [403, "You don't have permission to perform this action."],
      [404, 'The requested resource was not found.'],
      [408, 'Request timeout. Please try again.'],
      [429, 'Too many requests. Please wait a moment and try again.'],
      [500, 'Server error. Please try again later.'],
      [502, 'Service temporarily unavailable. Please try again later.'],
      [503, 'Service unavailable. Please try again later.'],
      [504, 'Request timeout. Please try again.'],
      [999, 'An unexpected error occurred. Please try again.'],
    ];

    test.each(statusMessages)('should return correct message for status %i', (status, expectedMessage) => {
      const { result } = renderHook(() => useErrorHandler());
      
      const error = {
        response: {
          status,
          data: {},
        },
      };
      
      const apiError = result.current.handleError(error);
      
      expect(apiError.message).toBe(expectedMessage);
    });
  });
});