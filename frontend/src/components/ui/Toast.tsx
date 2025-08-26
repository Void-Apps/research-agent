'use client';

import { toast, Toaster, ToastOptions } from 'react-hot-toast';

// Toast notification utilities
export const showToast = {
  success: (message: string, options?: ToastOptions) => {
    return toast.success(message, {
      duration: 4000,
      position: 'top-right',
      ...options,
    });
  },
  
  error: (message: string, options?: ToastOptions) => {
    return toast.error(message, {
      duration: 6000,
      position: 'top-right',
      ...options,
    });
  },
  
  loading: (message: string, options?: ToastOptions) => {
    return toast.loading(message, {
      position: 'top-right',
      ...options,
    });
  },
  
  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    },
    options?: ToastOptions
  ) => {
    return toast.promise(promise, messages, {
      position: 'top-right',
      ...options,
    });
  },
  
  dismiss: (toastId?: string) => {
    return toast.dismiss(toastId);
  },
};

// Toast container component
export function ToastContainer() {
  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      gutter={8}
      containerClassName=""
      containerStyle={{}}
      toastOptions={{
        // Default options for all toasts
        className: '',
        duration: 4000,
        style: {
          background: '#363636',
          color: '#fff',
          borderRadius: '8px',
          padding: '16px',
          fontSize: '14px',
          maxWidth: '500px',
        },
        
        // Success toast styling
        success: {
          style: {
            background: '#10b981',
            color: '#fff',
          },
          iconTheme: {
            primary: '#fff',
            secondary: '#10b981',
          },
        },
        
        // Error toast styling
        error: {
          style: {
            background: '#ef4444',
            color: '#fff',
          },
          iconTheme: {
            primary: '#fff',
            secondary: '#ef4444',
          },
        },
        
        // Loading toast styling
        loading: {
          style: {
            background: '#3b82f6',
            color: '#fff',
          },
        },
      }}
    />
  );
}

export default ToastContainer;