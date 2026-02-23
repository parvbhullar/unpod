'use client';

import React, {ReactNode} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';

export type AppDndProviderProps = {
  children: ReactNode;
};

const AppDndProvider: React.FC<AppDndProviderProps> = ({children}) => {
  return <DndProvider backend={HTML5Backend}>{children}</DndProvider>;
};

export default AppDndProvider;
