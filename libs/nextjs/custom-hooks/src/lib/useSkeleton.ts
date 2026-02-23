import {usePathname, useRouter} from 'next/navigation';
import {ComponentType, useEffect, useRef, useState} from 'react';

export type UseSkeletonResult<T extends ComponentType<unknown>> = {
  isPageLoading: boolean;
  skeleton: T;
};

export const useSkeleton = <T extends ComponentType<unknown>>(
  MainSkeleton: T,
  NewSkeleton: T,
  key = 'new',
): UseSkeletonResult<T> => {
  const router = useRouter();
  const pathname = usePathname();
  const nextPathRef = useRef<string | null>(null);
  const [isPageLoading, setIsPageLoading] = useState<boolean>(true);
  const [skeleton, setSkeleton] = useState<T>(
    pathname?.includes(key) ? NewSkeleton : MainSkeleton,
  );

  useEffect(() => {
    const originalPush = router.push;

    router.push = (...args: Parameters<typeof router.push>) => {
      nextPathRef.current = args[0];
      setIsPageLoading(false);
      setSkeleton(args[0].includes(key) ? NewSkeleton : MainSkeleton);
      return originalPush.apply(router, args);
    };

    if (nextPathRef.current === null) {
      setIsPageLoading(false);
    }

    return () => {
      router.push = originalPush;
    };
  }, [router, key, MainSkeleton, NewSkeleton]);

  return {isPageLoading, skeleton};
};
