'use client';

import { useState, ReactNode } from 'react';
import useIsomorphicLayoutEffect from '@/hooks/use-isomorphic-layout-effect';

interface ClientOnlyProps {
  children: ReactNode;
}

export default function ClientOnly({ children }: ClientOnlyProps) {
  const [hasMounted, setHasMounted] = useState(false);
  
  useIsomorphicLayoutEffect(() => {
    setHasMounted(true);
  }, []);
  
  // Only render children after component has mounted on client
  if (!hasMounted) {
    return null;
  }
  
  return <>{children}</>;
}