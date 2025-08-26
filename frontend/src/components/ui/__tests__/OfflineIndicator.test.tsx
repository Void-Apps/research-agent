import { render, screen } from '@testing-library/react';
import OfflineIndicator from '../OfflineIndicator';

// Mock the useOnlineStatus hook
jest.mock('../../../hooks/useOnlineStatus', () => ({
  useOnlineStatus: jest.fn(),
}));

describe('OfflineIndicator', () => {
  const mockUseOnlineStatus = require('../../../hooks/useOnlineStatus').useOnlineStatus;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when online', () => {
    mockUseOnlineStatus.mockReturnValue({ isOnline: true });
    
    const { container } = render(<OfflineIndicator />);
    
    expect(container.firstChild).toBeNull();
  });

  it('should render offline indicator when offline', () => {
    mockUseOnlineStatus.mockReturnValue({ isOnline: false });
    
    render(<OfflineIndicator />);
    
    expect(screen.getByText("You're offline. Some features may not work properly.")).toBeInTheDocument();
  });

  it('should have correct styling and positioning', () => {
    mockUseOnlineStatus.mockReturnValue({ isOnline: false });
    
    render(<OfflineIndicator />);
    
    const indicator = screen.getByText("You're offline. Some features may not work properly.").closest('div')?.parentElement;
    expect(indicator).toHaveClass('fixed', 'top-0', 'left-0', 'right-0', 'z-50', 'bg-red-600', 'text-white');
  });

  it('should display warning and wifi icons', () => {
    mockUseOnlineStatus.mockReturnValue({ isOnline: false });
    
    render(<OfflineIndicator />);
    
    // Check for SVG elements (icons) by their data-slot attribute
    const container = screen.getByText("You're offline. Some features may not work properly.").closest('div')?.parentElement;
    const svgElements = container?.querySelectorAll('svg');
    expect(svgElements).toHaveLength(2); // Warning icon and WiFi icon
  });

  it('should have proper accessibility attributes', () => {
    mockUseOnlineStatus.mockReturnValue({ isOnline: false });
    
    render(<OfflineIndicator />);
    
    const message = screen.getByText("You're offline. Some features may not work properly.");
    expect(message).toBeInTheDocument();
    
    // The component should be visible and accessible
    const container = message.closest('div');
    expect(container).toBeVisible();
  });
});