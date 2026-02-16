'use client';
import type { ComponentType, ForwardRefExoticComponent, HTMLAttributes, ReactNode, RefAttributes } from 'react';
import { useEffect, useRef, useState } from 'react';

/**
 * Common wrapper for all scrollable card containers
 * Handles scroll detection and conditional shadow display
 */
type ScrollComponentProps = HTMLAttributes<HTMLDivElement> & {
  $showLeftShadow?: boolean;
  $showRightShadow?: boolean;
};

type CardsScrollWrapperProps = {
  children: ReactNode;
  ScrollComponent: ComponentType<ScrollComponentProps>;
  items?: unknown[];
};

const CardsScrollWrapper = ({
  children,
  ScrollComponent,
  items = [],
}: CardsScrollWrapperProps) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [showLeftShadow, setShowLeftShadow] = useState(false);
  const [showRightShadow, setShowRightShadow] = useState(false);
  const ScrollComponentWithRef = ScrollComponent as ForwardRefExoticComponent<
    ScrollComponentProps & RefAttributes<HTMLDivElement>
  >;

  const checkScroll = () => {
    if (!scrollRef.current) return;

    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;

    // Show left shadow if scrolled away from left edge
    setShowLeftShadow(scrollLeft > 0);

    // Show right shadow if there's more content to the right
    setShowRightShadow(scrollLeft < scrollWidth - clientWidth - 1);
  };

  useEffect(() => {
    checkScroll();

    // Recheck on window resize
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [items]);

  return (
    <ScrollComponentWithRef
      ref={scrollRef}
      onScroll={checkScroll}
      $showLeftShadow={showLeftShadow}
      $showRightShadow={showRightShadow}
    >
      {children}
    </ScrollComponentWithRef>
  );
};

export default CardsScrollWrapper;
