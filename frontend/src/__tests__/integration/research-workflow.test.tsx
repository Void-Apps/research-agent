/**
 * Integration tests for complete research workflow
 */
import { screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../utils/testUtils'
import { mockApiResponses, createMockFetch } from '../fixtures/mockData'
import HomePage from '../../app/page'
import ResultsPage from '../../app/results/[id]/page'

// Mock the API
const mockFetch = createMockFetch(mockApiResponses.research.success.data)
global.fetch = mockFetch

describe('Research Workflow Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('should complete full research workflow from query to results', async () => {
    const user = userEvent.setup()
    
    // Step 1: Render home page
    render(<HomePage />)
    
    // Step 2: User enters research query
    const queryInput = screen.getByPlaceholderText(/enter your research topic/i)
    const submitButton = screen.getByRole('button', { name: /start research/i })
    
    await user.type(queryInput, 'artificial intelligence machine learning')
    expect(queryInput).toHaveValue('artificial intelligence machine learning')
    
    // Step 3: Submit research query
    await user.click(submitButton)
    
    // Step 4: Verify API call was made
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/research/query'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            query: 'artificial intelligence machine learning',
          }),
        })
      )
    })
    
    // Step 5: Verify loading state
    expect(screen.getByText(/researching/i)).toBeInTheDocument()
    
    // Step 6: Wait for results to load
    await waitFor(() => {
      expect(screen.getByText(/research completed/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('should handle research errors gracefully', async () => {
    const user = userEvent.setup()
    const errorFetch = createMockFetch(mockApiResponses.research.error.data, 400)
    global.fetch = errorFetch
    
    render(<HomePage />)
    
    const queryInput = screen.getByPlaceholderText(/enter your research topic/i)
    const submitButton = screen.getByRole('button', { name: /start research/i })
    
    await user.type(queryInput, 'invalid query')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/error occurred/i)).toBeInTheDocument()
    })
    
    // Verify retry functionality
    const retryButton = screen.getByRole('button', { name: /try again/i })
    expect(retryButton).toBeInTheDocument()
  })

  it('should display results correctly on results page', async () => {
    const mockParams = { id: 'test-query-123' }
    
    // Mock the results API call
    global.fetch = createMockFetch(mockApiResponses.research.success.data)
    
    render(<ResultsPage params={mockParams} />)
    
    // Wait for results to load
    await waitFor(() => {
      expect(screen.getByText(/research results/i)).toBeInTheDocument()
    })
    
    // Verify different source sections are displayed
    expect(screen.getByText(/google scholar/i)).toBeInTheDocument()
    expect(screen.getByText(/google books/i)).toBeInTheDocument()
    expect(screen.getByText(/sciencedirect/i)).toBeInTheDocument()
    
    // Verify AI summary is displayed
    expect(screen.getByText(/ai summary/i)).toBeInTheDocument()
    expect(screen.getByText(/significant advances in ai/i)).toBeInTheDocument()
  })

  it('should navigate between pages correctly', async () => {
    const user = userEvent.setup()
    
    render(<HomePage />)
    
    // Check navigation links
    const historyLink = screen.getByRole('link', { name: /history/i })
    expect(historyLink).toBeInTheDocument()
    expect(historyLink).toHaveAttribute('href', '/history')
  })

  it('should handle offline state', async () => {
    // Mock offline state
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    // Dispatch offline event
    window.dispatchEvent(new Event('offline'))
    
    render(<HomePage />)
    
    await waitFor(() => {
      expect(screen.getByText(/you are offline/i)).toBeInTheDocument()
    })
  })

  it('should persist research history', async () => {
    const user = userEvent.setup()
    
    // Mock history API
    global.fetch = createMockFetch(mockApiResponses.history.success.data)
    
    render(<HomePage />)
    
    // Navigate to history
    const historyLink = screen.getByRole('link', { name: /history/i })
    await user.click(historyLink)
    
    // Verify history is loaded
    await waitFor(() => {
      expect(screen.getByText(/research history/i)).toBeInTheDocument()
    })
    
    // Verify history items are displayed
    expect(screen.getByText(/machine learning algorithms/i)).toBeInTheDocument()
    expect(screen.getByText(/deep learning neural networks/i)).toBeInTheDocument()
  })
})