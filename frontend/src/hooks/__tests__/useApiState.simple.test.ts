import { renderHook, act, waitFor } from '@testing-library/react';
import { useApiConnection } from '../useApiState';

// Mock fetch
global.fetch = jest.fn();

// Mock useOnlineStatus
jest.mock('../useOnlineStatus', () => ({
  useOnlineStatus: jest.fn(() => true),
}));

describe('useApiState', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  describe('useApiConnection', () => {
    it('should check connection status', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
      });

      const { result } = renderHook(() => useApiConnection());

      expect(result.current.isOnline).toBe(true);

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(global.fetch).toHaveBeenCalledWith('/api/health', {
        method: 'HEAD',
        cache: 'no-cache',
      });
    });

    it('should handle connection failures', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useApiConnection());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false);
      });
    });

    it('should provide checkConnection function', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      const { result } = renderHook(() => useApiConnection());

      const isConnected = await act(async () => {
        return await result.current.checkConnection();
      });

      expect(isConnected).toBe(true);
    });

    it('should update lastConnected when connection succeeds', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      const { result } = renderHook(() => useApiConnection());

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
        expect(result.current.lastConnected).toBeInstanceOf(Date);
      });
    });

    it('should handle offline status', async () => {
      const { useOnlineStatus } = require('../useOnlineStatus');
      useOnlineStatus.mockReturnValue(false);

      const { result } = renderHook(() => useApiConnection());

      expect(result.current.isOnline).toBe(false);

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false);
      });
    });
  });
});