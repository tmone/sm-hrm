// src/app/page.tsx
'use client'; // Required for useRouter

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Skeleton } from '@/components/ui/skeleton'; // Optional: for a loading state

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/login'); // Redirect to login page
  }, [router]);

  // Optional: Show a loading state or a blank page during redirection
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
      <div className="space-y-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <Skeleton className="h-8 w-[250px]" />
        <Skeleton className="h-4 w-[200px]" />
      </div>
    </div>
  );
}
