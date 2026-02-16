'use client';
import React, { useState } from 'react';
import { useServerInsertedHTML } from 'next/navigation';
import { ServerStyleSheet, StyleSheetManager } from 'styled-components';
import type { LayoutProps } from '@/types/common';

export function StyledComponentsRegistry({ children }: LayoutProps) {
  // Only create stylesheet once with lazy initial state
  // x-ref: https://reactjs.org/docs/hooks-reference.html#lazy-initial-state
  const [styledComponentsStyleSheet] = useState(() => new ServerStyleSheet());
  useServerInsertedHTML(() => {
    const styles = styledComponentsStyleSheet.getStyleElement();
    // Types are out of date, clearTag is not defined.
    // See: https://github.com/DefinitelyTyped/DefinitelyTyped/issues/65021
    styledComponentsStyleSheet.instance.clearTag();
    return <>{styles}</>;
  });
  if (typeof window !== 'undefined') return <>{children}</>;
  return (
    <StyleSheetManager sheet={styledComponentsStyleSheet.instance}>
      {children}
    </StyleSheetManager>
  );
}
