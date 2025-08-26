import { render, screen, waitFor } from '@testing-library/react';
import { showToast, ToastContainer } from '../Toast';

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    promise: jest.fn(),
    dismiss: jest.fn(),
  },
  Toaster: ({ children }: { children?: React.ReactNode }) => <div data-testid="toaster">{children}</div>,
}));

describe('Toast', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('showToast utilities', () => {
    it('should call toast.success with correct parameters', () => {
      const mockToast = require('react-hot-toast').toast;
      
      showToast.success('Success message');
      
      expect(mockToast.success).toHaveBeenCalledWith('Success message', {
        duration: 4000,
        position: 'top-right',
      });
    });

    it('should call toast.error with correct parameters', () => {
      const mockToast = require('react-hot-toast').toast;
      
      showToast.error('Error message');
      
      expect(mockToast.error).toHaveBeenCalledWith('Error message', {
        duration: 6000,
        position: 'top-right',
      });
    });

    it('should call toast.loading with correct parameters', () => {
      const mockToast = require('react-hot-toast').toast;
      
      showToast.loading('Loading message');
      
      expect(mockToast.loading).toHaveBeenCalledWith('Loading message', {
        position: 'top-right',
      });
    });

    it('should call toast.promise with correct parameters', () => {
      const mockToast = require('react-hot-toast').toast;
      const promise = Promise.resolve('data');
      const messages = {
        loading: 'Loading...',
        success: 'Success!',
        error: 'Error!',
      };
      
      showToast.promise(promise, messages);
      
      expect(mockToast.promise).toHaveBeenCalledWith(promise, messages, {
        position: 'top-right',
      });
    });

    it('should call toast.dismiss with correct parameters', () => {
      const mockToast = require('react-hot-toast').toast;
      
      showToast.dismiss('toast-id');
      
      expect(mockToast.dismiss).toHaveBeenCalledWith('toast-id');
    });

    it('should accept custom options', () => {
      const mockToast = require('react-hot-toast').toast;
      const customOptions = { duration: 8000, position: 'bottom-left' as const };
      
      showToast.success('Message', customOptions);
      
      expect(mockToast.success).toHaveBeenCalledWith('Message', {
        duration: 8000,
        position: 'bottom-left',
      });
    });
  });

  describe('ToastContainer', () => {
    it('should render Toaster component', () => {
      render(<ToastContainer />);
      
      expect(screen.getByTestId('toaster')).toBeInTheDocument();
    });
  });
});