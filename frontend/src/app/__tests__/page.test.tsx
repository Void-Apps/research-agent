import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import Home from '../page';
import { useSubmitResearch } from '@/hooks/useResearch';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('@/hooks/useResearch', () => ({
  useSubmitResearch: jest.fn(),
}));

jest.mock('@/components/layout/MainLayout', () => {
  return function MockMainLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="main-layout">{children}</div>;
  };
});

jest.mock('@/components/ResearchForm', () => {
  return function MockResearchForm({ 
    onSubmit, 
    isLoading 
  }: { 
    onSubmit: (query: string) => void; 
    isLoading?: boolean; 
  }) {
    return (
      <div data-testid="research-form">
        <button
          onClick={() => onSubmit('test query')}
          disabled={isLoading}
          data-testid="submit-button"
        >
          {isLoading ? 'Loading...' : 'Submit'}
        </button>
      </div>
    );
  };
});

const mockPush = jest.fn();
const mockMutateAsync = jest.fn();

describe('Home Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
    (useSubmitResearch as jest.Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    });
  });

  it('renders the home page with title and description', () => {
    render(<Home />);
    
    expect(screen.getByText('AI Research Agent')).toBeInTheDocument();
    expect(screen.getByText(/Submit your research requirements/)).toBeInTheDocument();
    expect(screen.getByTestId('research-form')).toBeInTheDocument();
  });

  it('handles successful research submission', async () => {
    const mockResult = { id: 'test-query-id' };
    mockMutateAsync.mockResolvedValue(mockResult);

    render(<Home />);
    
    const submitButton = screen.getByTestId('submit-button');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({ query: 'test query' });
      expect(toast.success).toHaveBeenCalledWith('Research query submitted successfully!');
      expect(mockPush).toHaveBeenCalledWith('/results/test-query-id');
    });
  });

  it('handles research submission error', async () => {
    const mockError = new Error('Submission failed');
    mockMutateAsync.mockRejectedValue(mockError);

    render(<Home />);
    
    const submitButton = screen.getByTestId('submit-button');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({ query: 'test query' });
      expect(toast.error).toHaveBeenCalledWith('Failed to submit research query. Please try again.');
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it('shows loading state during submission', () => {
    (useSubmitResearch as jest.Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
    });

    render(<Home />);
    
    const submitButton = screen.getByTestId('submit-button');
    expect(submitButton).toHaveTextContent('Loading...');
    expect(submitButton).toBeDisabled();
  });
});