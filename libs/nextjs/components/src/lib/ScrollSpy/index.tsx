'use client';

import React, { useEffect, useState, useRef } from 'react';

export type ScrollSpyProps = {
  items?: string[];
  currentClassName?: string;
  className?: string;
  offset?: number;
  children?: React.ReactNode;
  [key: string]: unknown;
};

const ScrollSpy: React.FC<ScrollSpyProps> = ({
  items = [],
  currentClassName = 'is-current',
  className,
  offset = 0,
  children,
  ...rest
}) => {
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (!items.length) return;

    const handleScroll = () => {
      const scrollTop = window.scrollY + offset;
      let currentIndex = -1;

      for (let i = items.length - 1; i >= 0; i--) {
        const el = document.getElementById(items[i]);
        if (el && el.offsetTop <= scrollTop) {
          currentIndex = i;
          break;
        }
      }

      setActiveIndex(currentIndex);
    };

    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [items, offset]);

  const childArray = React.Children.toArray(children);

  return (
    <ul ref={containerRef} className={className} {...rest}>
      {childArray.map((child, index) => {
        if (!React.isValidElement(child)) return child;
        const childClassName = [
          (child.props as { className?: string }).className,
          index === activeIndex ? currentClassName : '',
        ]
          .filter(Boolean)
          .join(' ');
        return React.cloneElement(child as React.ReactElement<{ className?: string }>, {
          className: childClassName || undefined,
        });
      })}
    </ul>
  );
};

export default ScrollSpy;
