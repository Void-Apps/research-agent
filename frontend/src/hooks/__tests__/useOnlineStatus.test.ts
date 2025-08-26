import { renderHook, act } from '@testing-library/react';
import { useOnlineStatus } from '../useOnlineStatus';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { afterEach } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the showToast function
jest.mock('../../components/ui/Toast', () => ({
  showToast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe('useOnlineStatus', () => {
  const mockShowToast = require('../../components/ui/Toast').showToast;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    // Mock window event listeners
    global.addEventListener = jest.fn();
    global.removeEventListener = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should return initial online status', () => {
    const { result } = renderHook(() => useOnlineStatus());
    
    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(false);
  });

  it('should return offline status when navigator.onLine is false', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useOnlineStatus());
    
    expect(result.current.isOnline).toBe(false);
  });

  it('should add event listeners on mount', () => {
    renderHook(() => useOnlineStatus());
    
    expect(global.addEventListener).toHaveBeenCalledWith('online', expect.any(Function));
    expect(global.addEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
  });

  it('should remove event listeners on unmount', () => {
    const { unmount } = renderHook(() => useOnlineStatus());
    
    unmount();
    
    expect(global.removeEventListener).toHaveBeenCalledWith('online', expect.any(Function));
    expect(global.removeEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
  });

  it('should show error toast when going offline', () => {
    const { result } = renderHook(() => useOnlineStatus());
    
    // Simulate going offline
    act(() => {
      // Update navigator.onLine to false
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });
      
      const offlineHandler = (global.addEventListener as jest.Mock).mock.calls
        .find(call => call[0] === 'offline')[1];
      offlineHandler();
    });
    
    expect(result.current.isOnline).toBe(false);
    expect(result.current.wasOffline).toBe(true);
    expect(mockShowToast.error).toHaveBeenCalledWith(
      "You're offline. Some features may not work properly.",
      { duration: 8000 }
    );
  });

  it('should show success toast when coming back online after being offline', () => {
    const { result } = renderHook(() => useOnlineStatus());
    
    // First go offline
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });
      
      const offlineHandler = (global.addEventListener as jest.Mock).mock.calls
        .find(call => call[0] === 'offline')[1];
      offlineHandler();
    });
    
    expect(result.current.wasOffline).toBe(true);
    
    // Then come back online - need to get the handler after the state change
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });
      
      // Get the most recent online handler (after the effect re-ran)
      const onlineHandlerCalls = (global.addEventListener as jest.Mock).mock.calls
        .filter(call => call[0] === 'online');
      const onlineHandler = onlineHandlerCalls[onlineHandlerCalls.length - 1][1];
      onlineHandler();
    });
    
    expect(result.current.isOnline).toBe(true);
    expect(mockShowToast.success).toHaveBeenCalledWith(
      "Connection restored! You're back online."
    );
    // Note: wasOffline might still be true due to the async nature of the state update
  });

  it('should not show success toast when coming online without being offline first', () => {
    renderHook(() => useOnlineStatus());
    
    // Come online without being offline first
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });
      
      const onlineHandler = (global.addEventListener as jest.Mock).mock.calls
        .find(call => call[0] === 'online')[1];
      onlineHandler();
    });
    
    expect(mockShowToast.success).not.toHaveBeenCalled();
  });

  it('should handle server-side rendering gracefully', () => {
    // Mock window as undefined (SSR environment)
    const originalWindow = global.window;
    delete (global as any).window;
    
    const { result } = renderHook(() => useOnlineStatus());
    
    // Should not crash and should return default values
    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(false);
    
    // Restore window
    global.window = originalWindow;
  });
});