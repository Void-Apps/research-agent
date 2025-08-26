import { render, screen } from '@testing-library/react';
import Breadcrumb from '../Breadcrumb';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
    return <a href={href} className={className}>{children}</a>;
  };
});

// Mock Heroicons
jest.mock('@heroicons/react/20/solid', () => ({
  ChevronRightIcon: function MockChevronRightIcon({ className }: { className?: string }) {
    return <div data-testid="chevron-right" className={className}>→</div>;
  },
  HomeIcon: function MockHomeIcon({ className }: { className?: string }) {
    return <div data-testid="home-icon" className={className}>🏠</div>;
  },
}));

describe('Breadcrumb Component', () => {
  it('renders home icon and link', () => {
    const items = [
      { label: 'Test Page', current: true }
    ];

    render(<Breadcrumb items={items} />);
    
    expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Home/i })).toHaveAttribute('href', '/');
  });

  it('renders breadcrumb items with links', () => {
    const items = [
      { label: 'First Page', href: '/first' },
      { label: 'Second Page', href: '/second' },
      { label: 'Current Page', current: true }
    ];

    render(<Breadcrumb items={items} />);
    
    expect(screen.getByRole('link', { name: 'First Page' })).toHaveAttribute('href', '/first');
    expect(screen.getByRole('link', { name: 'Second Page' })).toHaveAttribute('href', '/second');
    expect(screen.getByText('Current Page')).toBeInTheDocument();
  });

  it('renders current page without link', () => {
    const items = [
      { label: 'Current Page', current: true }
    ];

    render(<Breadcrumb items={items} />);
    
    const currentPage = screen.getByText('Current Page');
    expect(currentPage).toBeInTheDocument();
    expect(currentPage.tagName).toBe('SPAN');
    expect(currentPage).toHaveAttribute('aria-current', 'page');
  });

  it('renders chevron separators', () => {
    const items = [
      { label: 'First Page', href: '/first' },
      { label: 'Current Page', current: true }
    ];

    render(<Breadcrumb items={items} />);
    
    const chevrons = screen.getAllByTestId('chevron-right');
    expect(chevrons).toHaveLength(2); // One for home, one for first page
  });

  it('applies correct styling for current page', () => {
    const items = [
      { label: 'Previous Page', href: '/previous' },
      { label: 'Current Page', current: true }
    ];

    render(<Breadcrumb items={items} />);
    
    const currentPage = screen.getByText('Current Page');
    expect(currentPage).toHaveClass('text-gray-900');
    
    const previousPage = screen.getByText('Previous Page');
    expect(previousPage).toHaveClass('text-gray-500');
  });

  it('handles items without href correctly', () => {
    const items = [
      { label: 'No Link Page' },
      { label: 'Current Page', current: true }
    ];

    render(<Breadcrumb items={items} />);
    
    const noLinkPage = screen.getByText('No Link Page');
    expect(noLinkPage.tagName).toBe('SPAN');
    expect(noLinkPage).not.toHaveAttribute('href');
  });
});