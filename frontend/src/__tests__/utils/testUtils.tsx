/**
 * Test utilities for React Testing Library
 */
import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// Custom matchers and utilities
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0))
}

export const mockConsoleError = () => {
  const originalError = console.error
  const mockError = jest.fn()
  console.error = mockError
  
  return {
    mockError,
    restore: () => {
      console.error = originalError
    },
  }
}

export const mockConsoleWarn = () => {
  const originalWarn = console.warn
  const mockWarn = jest.fn()
  console.warn = mockWarn
  
  return {
    mockWarn,
    restore: () => {
      console.warn = originalWarn
    },
  }
}

// Mock router utilities
export const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
}

export const mockSearchParams = new URLSearchParams()

// Test data generators
export const generateMockId = () => `test-${Math.random().toString(36).substr(2, 9)}`

export const generateMockTimestamp = () => new Date().toISOString()

// Async test helpers
export const flushPromises = () => new Promise(resolve => setImmediate(resolve))

export const act = async (callback: () => void | Promise<void>) => {
  const { act: rtlAct } = await import('@testing-library/react')
  await rtlAct(callback)
}