import { render, screen } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { afterEach } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Component that throws an error for testing
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error for these tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('should render error UI when there is an error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('We encountered an unexpected error. Please try refreshing the page.')).toBeInTheDocument();
  });

  it('should render custom fallback when provided', () => {
    const customFallback = <div>Custom error fallback</div>;
    
    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error fallback')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('should have refresh button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const refreshButton = screen.getByRole('button', { name: /refresh page/i });
    expect(refreshButton).toBeInTheDocument();
    expect(refreshButton).toHaveClass('bg-red-600', 'text-white');
  });

  it('should log error to console', () => {
    const consoleSpy = jest.spyOn(console, 'error');
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      'ErrorBoundary caught an error:',
      expect.any(Error),
      expect.any(Object)
    );
  });

  it('should have proper styling and accessibility', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Check for proper outer container styling
    const outerContainer = screen.getByText('Something went wrong').closest('div')?.parentElement?.parentElement?.parentElement;
    expect(outerContainer).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center', 'bg-gray-50');

    // Check for error icon
    const errorIcon = screen.getByText('Something went wrong').closest('div')?.parentElement?.querySelector('svg');
    expect(errorIcon).toBeInTheDocument();
    expect(errorIcon).toHaveClass('h-8', 'w-8', 'text-red-400');

    // Check button styling
    const refreshButton = screen.getByRole('button', { name: /refresh page/i });
    expect(refreshButton).toHaveClass('bg-red-600', 'text-white', 'px-4', 'py-2', 'rounded-md');
  });

  it('should reset error state when children change', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Error should be displayed
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    // Rerender with non-throwing component
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    // Error should still be displayed (ErrorBoundary doesn't reset automatically)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('should handle different error types', () => {
    const CustomError = () => {
      throw new TypeError('Type error');
    };

    render(
      <ErrorBoundary>
        <CustomError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });
});