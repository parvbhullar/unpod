'use client';

import {RefObject, useEffect} from 'react';

export const useOutsideClick = <T extends HTMLElement>(
  ref: RefObject<T | null>,
  callback: () => void,
): void => {
  const handleClick = (e: MouseEvent): void => {
    if (ref.current && !ref.current.contains(e.target as Node)) {
      callback();
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  });
};
