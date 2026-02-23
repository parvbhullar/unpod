'use client';

import {DependencyList, RefObject, useEffect, useRef, useState} from 'react';

export type Boundary = {
  width: number;
  height: number;
  top?: number;
  left?: number;
  right?: number;
  bottom?: number;
  x?: number;
  y?: number;
};

export type UseMeasureResult<T extends HTMLElement = HTMLElement> = [
  Boundary,
  RefObject<T | null>,
];

export const useMeasure = <T extends HTMLElement = HTMLElement>(
  deps: DependencyList = [],
): UseMeasureResult<T> => {
  const [boundary, setBoundary] = useState<Boundary>({width: 0, height: 0});
  const elementRef = useRef<T | null>(null);

  useEffect(() => {
    const rect = elementRef.current?.getBoundingClientRect();
    if (rect) {
      setBoundary(rect);
    }
  }, deps);

  useEffect(() => {
    // Handler to call on window resize
    function handleResize(): void {
      // Set window width/height to state
      const rect = elementRef.current?.getBoundingClientRect();
      if (rect) {
        setBoundary(rect);
      }
    }

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Remove event listener on cleanup
    return () => window.removeEventListener('resize', handleResize);
  }, []); // Empty array ensures that effect is only run on mount

  return [boundary, elementRef];
};
