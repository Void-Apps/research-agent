/**
 * Tests for page structure and navigation elements without external dependencies
 */

import { render, screen } from '@testing-library/react';

// Mock Next.js components
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

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

describe('Page Structure Tests', () => {
  describe('Breadcrumb Component', () => {
    it('renders breadcrumb with home link and items', async () => {
      const Breadcrumb = (await import('@/components/ui/Breadcrumb')).default;
      const items = [
        { label: 'First Page', href: '/first' },
        { label: 'Current Page', current: true }
      ];
      
      render(<Breadcrumb items={items} />);
      
      // Check home link
      const homeLink = screen.getByRole('link', { name: /Home/i });
      expect(homeLink).toHaveAttribute('href', '/');
      
      // Check breadcrumb items
      expect(screen.getByText('First Page')).toBeInTheDocument();
      expect(screen.getByText('Current Page')).toBeInTheDocument();
      
      // Check chevron separators
      expect(screen.getAllByTestId('chevron-right')).toHaveLength(2);
    });

    it('handles current page correctly', async () => {
      const Breadcrumb = (await import('@/components/ui/Breadcrumb')).default;
      const items = [{ label: 'Current Page', current: true }];
      
      render(<Breadcrumb items={items} />);
      
      const currentPage = screen.getByText('Current Page');
      expect(currentPage).toHaveAttribute('aria-current', 'page');
      expect(currentPage.tagName).toBe('SPAN');
    });
  });

  describe('Layout Components', () => {
    it('renders MainLayout with header navigation', async () => {
      const MainLayout = (await import('@/components/layout/MainLayout')).default;
      
      render(
        <MainLayout>
          <div>Test Content</div>
        </MainLayout>
      );
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders Header with navigation links', async () => {
      const Header = (await import('@/components/layout/Header')).default;
      
      render(<Header />);
      
      expect(screen.getByText('AI Research Agent')).toBeInTheDocument();
      
      const researchLink = screen.getByRole('link', { name: 'Research' });
      const historyLink = screen.getByRole('link', { name: 'History' });
      
      expect(researchLink).toHaveAttribute('href', '/');
      expect(historyLink).toHaveAttribute('href', '/history');
    });

    it('renders Footer with correct content', async () => {
      const Footer = (await import('@/components/layout/Footer')).default;
      
      render(<Footer />);
      
      expect(screen.getByText(/© 2025 AI Research Agent/)).toBeInTheDocument();
      expect(screen.getByText(/Powered by AI and multiple academic sources/)).toBeInTheDocument();
    });
  });
});