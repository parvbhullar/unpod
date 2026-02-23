import React from 'react';
import type {Maybe} from '../models/data-grid';

export function stopPropagation(event: React.SyntheticEvent) {
  event.stopPropagation();
}

export function scrollIntoView(element: Maybe<Element>) {
  element?.scrollIntoView({inline: 'nearest', block: 'nearest'});
}
