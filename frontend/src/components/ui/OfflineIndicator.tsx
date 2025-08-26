'use client';

import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { ExclamationTriangleIcon, WifiIcon } from '@heroicons/react/24/outline';

export default function OfflineIndicator() {
  const { isOnline } = useOnlineStatus();

  if (isOnline) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white px-4 py-2">
      <div className="flex items-center justify-center space-x-2">
        <ExclamationTriangleIcon className="h-5 w-5" />
        <span className="text-sm font-medium">
          You're offline. Some features may not work properly.
        </span>
        <WifiIcon className="h-5 w-5 opacity-50" />
      </div>
    </div>
  );
}