import React from 'react';
import type {RenderCellProps} from '../models/data-grid';

export function renderValue<R, SR>(props: RenderCellProps<R, SR>) {
  try {
    return props.row[props.column.dataIndex as keyof R] as React.ReactNode;
  } catch {
    return null;
  }
}
