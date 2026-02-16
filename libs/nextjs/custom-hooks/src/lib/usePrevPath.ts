'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';

type PathRef = {
  current: string;
  previous: string | null;};

export const usePreviousPath = (): string | null => {
  const pathname = usePathname();
  const ref = useRef<PathRef>({ current: pathname, previous: null });

  useEffect(() => {
    if (ref.current.current !== pathname) {
      ref.current.previous = ref.current.current;
      ref.current.current = pathname;
    }
  }, [pathname]);

  return ref.current.previous;
};
