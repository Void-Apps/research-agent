import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ResearchForm from '../ResearchForm';
import { useSubmitResearch } from '../../hooks/useResearch';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the useSubmitResearch hook
jest.mock('../../hooks/useResearch', () => ({
  useSubmitResearch: jest.fn(),
}));

const mockUseSubmitResearch = useSubmitResearch as jest.MockedFunction<typeof useSubmitResearch>;

// Test wrapper with React Query provider
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ResearchForm', () => {
  const mockMutateAsync = jest.fn();
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSubmitResearch.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
      data: undefined,
      isSuccess: false,
      isIdle: true,
      failureCount: 0,
      failureReason: null,
      mutate: jest.fn(),
      reset: jest.fn(),
      status: 'idle',
      variables: undefined,
      context: undefined,
      submittedAt: 0,
    });
  });

  const renderResearchForm = (props = {}) => {
    return render(
      <TestWrapper>
        <ResearchForm onSubmit={mockOnSubmit} {...props} />
      </TestWrapper>
    );
  };

  describe('Rendering', () => {
    it('renders the form with all required elements', () => {
      renderResearchForm();

      expect(screen.getByLabelText(/research query/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/enter your research topic/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start research/i })).toBeInTheDocument();
      expect(screen.getByText(/our ai will search/i)).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      const { container } = renderResearchForm({ className: 'custom-class' });
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('shows character count', () => {
      renderResearchForm();
      expect(screen.getByText('0/500')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows error for empty query', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      expect(screen.getByText(/research query is required/i)).toBeInTheDocument();
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('shows error for query too short', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, 'AI');

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      expect(screen.getByText(/research query must be at least 3 characters long/i)).toBeInTheDocument();
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('shows error for query too long', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const longQuery = 'a'.repeat(501);
      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, longQuery);

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      expect(screen.getByText(/research query must be less than 500 characters/i)).toBeInTheDocument();
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('clears validation errors when user starts typing', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      const submitButton = screen.getByRole('button', { name: /start research/i });

      // Trigger validation error
      await user.click(submitButton);
      expect(screen.getByText(/research query is required/i)).toBeInTheDocument();

      // Start typing to clear error
      await user.type(textarea, 'machine learning');
      expect(screen.queryByText(/research query is required/i)).not.toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('submits valid query successfully', async () => {
      const user = userEvent.setup();
      const mockResult = { id: 'query-123' };
      mockMutateAsync.mockResolvedValue(mockResult);

      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, 'machine learning applications');

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          query: 'machine learning applications',
        });
      });

      expect(mockOnSubmit).toHaveBeenCalledWith('query-123');
    });

    it('trims whitespace from query before submission', async () => {
      const user = userEvent.setup();
      const mockResult = { id: 'query-123' };
      mockMutateAsync.mockResolvedValue(mockResult);

      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, '  machine learning  ');

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          query: 'machine learning',
        });
      });
    });

    it('clears form after successful submission', async () => {
      const user = userEvent.setup();
      const mockResult = { id: 'query-123' };
      mockMutateAsync.mockResolvedValue(mockResult);

      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, 'machine learning');

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(textarea).toHaveValue('');
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during submission', () => {
      mockUseSubmitResearch.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isError: false,
        error: null,
        data: undefined,
        isSuccess: false,
        isIdle: false,
        failureCount: 0,
        failureReason: null,
        mutate: jest.fn(),
        reset: jest.fn(),
        status: 'pending',
        variables: undefined,
        context: undefined,
        submittedAt: Date.now(),
      });

      renderResearchForm();

      expect(screen.getByText(/processing research/i)).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('disables form elements during loading', () => {
      mockUseSubmitResearch.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isError: false,
        error: null,
        data: undefined,
        isSuccess: false,
        isIdle: false,
        failureCount: 0,
        failureReason: null,
        mutate: jest.fn(),
        reset: jest.fn(),
        status: 'pending',
        variables: undefined,
        context: undefined,
        submittedAt: Date.now(),
      });

      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      const submitButton = screen.getByRole('button');

      expect(textarea).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });

    it('shows loading indicator in textarea during submission', () => {
      mockUseSubmitResearch.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isError: false,
        error: null,
        data: undefined,
        isSuccess: false,
        isIdle: false,
        failureCount: 0,
        failureReason: null,
        mutate: jest.fn(),
        reset: jest.fn(),
        status: 'pending',
        variables: undefined,
        context: undefined,
        submittedAt: Date.now(),
      });

      renderResearchForm();

      // Check for loading indicator (spinner) in the textarea area
      const loadingIndicator = document.querySelector('.animate-spin');
      expect(loadingIndicator).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('displays error message when submission fails', () => {
      const errorMessage = 'Network error occurred';
      mockUseSubmitResearch.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: true,
        error: { message: errorMessage },
        data: undefined,
        isSuccess: false,
        isIdle: false,
        failureCount: 1,
        failureReason: { message: errorMessage },
        mutate: jest.fn(),
        reset: jest.fn(),
        status: 'error',
        variables: undefined,
        context: undefined,
        submittedAt: Date.now(),
      });

      renderResearchForm();

      expect(screen.getByText(/research submission failed/i)).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('displays default error message when no specific error message', () => {
      mockUseSubmitResearch.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: true,
        error: {},
        data: undefined,
        isSuccess: false,
        isIdle: false,
        failureCount: 1,
        failureReason: {},
        mutate: jest.fn(),
        reset: jest.fn(),
        status: 'error',
        variables: undefined,
        context: undefined,
        submittedAt: Date.now(),
      });

      renderResearchForm();

      expect(screen.getByText(/failed to submit research query/i)).toBeInTheDocument();
    });
  });

  describe('Character Count', () => {
    it('updates character count as user types', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, 'hello');

      expect(screen.getByText('5/500')).toBeInTheDocument();
    });

    it('shows red color when approaching character limit', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const longQuery = 'a'.repeat(451);
      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, longQuery);

      const characterCount = screen.getByText('451/500');
      expect(characterCount).toHaveClass('text-red-500');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and descriptions', () => {
      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      expect(textarea).toHaveAttribute('aria-invalid', 'false');
    });

    it('sets aria-invalid to true when there are validation errors', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      const textarea = screen.getByLabelText(/research query/i);
      expect(textarea).toHaveAttribute('aria-invalid', 'true');
      expect(textarea).toHaveAttribute('aria-describedby', 'query-error');
    });

    it('has proper role attributes for error messages', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const submitButton = screen.getByRole('button', { name: /start research/i });
      await user.click(submitButton);

      const errorMessage = screen.getByText(/research query is required/i);
      expect(errorMessage).toHaveAttribute('role', 'alert');
    });
  });

  describe('Responsive Design', () => {
    it('applies responsive classes correctly', () => {
      const { container } = renderResearchForm();
      
      // Check for responsive container classes
      expect(container.querySelector('.max-w-4xl')).toBeInTheDocument();
      expect(container.querySelector('.mx-auto')).toBeInTheDocument();
    });
  });

  describe('Button States', () => {
    it('shows visual feedback when query is empty', () => {
      renderResearchForm();

      const submitButton = screen.getByRole('button', { name: /start research/i });
      expect(submitButton).not.toBeDisabled();
      expect(submitButton).toHaveClass('bg-gray-400');
    });

    it('shows active state when query has content', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, 'test query');

      const submitButton = screen.getByRole('button', { name: /start research/i });
      expect(submitButton).not.toBeDisabled();
      expect(submitButton).toHaveClass('bg-blue-600');
    });

    it('shows visual feedback when only whitespace is entered', async () => {
      const user = userEvent.setup();
      renderResearchForm();

      const textarea = screen.getByLabelText(/research query/i);
      await user.type(textarea, '   ');

      const submitButton = screen.getByRole('button', { name: /start research/i });
      expect(submitButton).not.toBeDisabled();
      expect(submitButton).toHaveClass('bg-gray-400');
    });
  });
});