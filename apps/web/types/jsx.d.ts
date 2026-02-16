import type { ReactElement } from 'react';

declare global {
  namespace JSX {
    type Element = ReactElement;
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

export {};
