'use client';
import React, { ReactNode } from 'react';
import GridFooter from './GridFooter';
import GridView from './GridView';
import ListEmptyResult from '../AppList/ListEmptyResult';

type AppGridProps<T> = {
  border?: boolean;
  containerStyle?: React.CSSProperties;
  footerProps?: {
    loading: boolean;
    footerText: string;
  };
  ListEmptyComponent?: ReactNode;
  ListFooterComponent?: ReactNode;
  data: T[];
  onEndReached?: () => void;
  renderItem: (item: T, index: number) => ReactNode;
  [key: string]: unknown;
};

const AppGrid = <T,>({
  footerProps,
  ...rest
}: AppGridProps<T>) => {
  return (
    <GridView<T>
      {...rest}
      ListFooterComponent={
        footerProps ? (
          <GridFooter
            loading={footerProps.loading}
            footerText={footerProps.footerText}
          />
        ) : null
      }
      ListEmptyComponent={<ListEmptyResult {...rest}></ListEmptyResult>}
    />
  );
};

export default AppGrid;
