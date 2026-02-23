import React from 'react';
import type {CellEvent} from '../models/data-grid';

export function createCellEvent<E extends React.SyntheticEvent<HTMLDivElement>>(
  event: E,
): CellEvent<E> {
  let defaultPrevented = false;
  const cellEvent = {
    ...event,
    preventGridDefault() {
      defaultPrevented = true;
    },
    isGridDefaultPrevented() {
      return defaultPrevented;
    },
  };

  Object.setPrototypeOf(cellEvent, Object.getPrototypeOf(event));

  return cellEvent;
}
