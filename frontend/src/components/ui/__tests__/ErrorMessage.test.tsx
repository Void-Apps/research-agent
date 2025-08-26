import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ErrorMessage from '../ErrorMessage';

describe('ErrorMessage', () => {
  const defaultProps = {
    message: 'Test error message',
  };

  it('should render error message with default title', () => {
    render(<ErrorMessage {...defaultProps} />);
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should render custom title when provided', () => {
    render(<ErrorMessage {...defaultProps} title="Custom Error Title" />);
    
    expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should render retry button when onRetry is provided', () => {
    const mockRetry = jest.fn();
    render(<ErrorMessage {...defaultProps} onRetry={mockRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /try again/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should not render retry button when showRetry is false', () => {
    const mockRetry = jest.fn();
    render(<ErrorMessage {...defaultProps} onRetry={mockRetry} showRetry={false} />);
    
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const mockRetry = jest.fn();
    render(<ErrorMessage {...defaultProps} onRetry={mockRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryButton);
    
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  it('should show loading state during retry', async () => {
    const mockRetry = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<ErrorMessage {...defaultProps} onRetry={mockRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /try again/i });
    
    await act(async () => {
      fireEvent.click(retryButton);
    });
    
    expect(screen.getByText('Retrying...')).toBeInTheDocument();
    expect(retryButton).toBeDisabled();
    
    await waitFor(() => {
      expect(screen.getByText('Try again')).toBeInTheDocument();
      expect(retryButton).not.toBeDisabled();
    });
  });

  it('should render custom retry text', () => {
    const mockRetry = jest.fn();
    render(<ErrorMessage {...defaultProps} onRetry={mockRetry} retryText="Retry Now" />);
    
    expect(screen.getByRole('button', { name: /retry now/i })).toBeInTheDocument();
  });

  it('should apply correct variant classes', () => {
    const { rerender } = render(<ErrorMessage {...defaultProps} variant="inline" />);
    let container = screen.getByText('Test error message').closest('div')?.parentElement?.parentElement;
    expect(container).toHaveClass('p-3', 'bg-red-50', 'border', 'border-red-200', 'rounded-md');

    rerender(<ErrorMessage {...defaultProps} variant="card" />);
    container = screen.getByText('Test error message').closest('div')?.parentElement?.parentElement;
    expect(container).toHaveClass('p-6', 'bg-white', 'border', 'border-red-200', 'rounded-lg', 'shadow-sm');

    rerender(<ErrorMessage {...defaultProps} variant="banner" />);
    container = screen.getByText('Test error message').closest('div')?.parentElement?.parentElement;
    expect(container).toHaveClass('p-4', 'bg-red-50', 'border-l-4', 'border-red-400');
  });

  it('should apply custom className', () => {
    render(<ErrorMessage {...defaultProps} className="custom-class" />);
    
    const container = screen.getByText('Test error message').closest('div')?.parentElement?.parentElement;
    expect(container).toHaveClass('custom-class');
  });

  it('should handle async retry function errors gracefully', async () => {
    const mockRetry = jest.fn(() => Promise.reject(new Error('Retry failed')));
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    render(<ErrorMessage {...defaultProps} onRetry={mockRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /try again/i });
    
    await act(async () => {
      fireEvent.click(retryButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Try again')).toBeInTheDocument();
      expect(retryButton).not.toBeDisabled();
    });
    
    expect(consoleSpy).toHaveBeenCalledWith('Retry failed:', expect.any(Error));
    consoleSpy.mockRestore();
  });
});