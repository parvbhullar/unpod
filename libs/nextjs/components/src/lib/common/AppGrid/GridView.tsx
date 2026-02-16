import React, { ReactNode, useEffect, useState } from 'react';
import { useBottomScrollListener } from 'react-bottom-scroll-listener';
import { Grid } from 'antd';
// import AppAnimateGroup from '../AppAnimateGroup';
import { StyledGridColumnCount, StyledGridContainer } from './index.styled';

const { useBreakpoint } = Grid;

const getEmptyContainer = (ListEmptyComponent: ReactNode) => {
  if (ListEmptyComponent)
    return React.isValidElement(ListEmptyComponent) ? (
      ListEmptyComponent
    ) : (
      <>{ListEmptyComponent}</>
    );
  return null;
};

const getFooterContainer = (ListFooterComponent: ReactNode) => {
  if (ListFooterComponent)
    return React.isValidElement(ListFooterComponent) ? (
      ListFooterComponent
    ) : (
      <>{ListFooterComponent}</>
    );
  return null;
};

type GridViewProps<T> = {
  column?: number;
  responsive?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    xxl?: number;
  };
  itemPadding?: number;
  renderItem: (item: T, index: number) => ReactNode;
  onEndReached?: () => void;
  data?: T[];
  containerStyle?: React.CSSProperties;
  border?: boolean;
  ListFooterComponent?: ReactNode;
  ListEmptyComponent?: ReactNode;
};

const GridView = <T,>({
  column = 3,
  responsive,
  itemPadding = 12,
  renderItem,
  onEndReached = () => {
    console.log('onEndReached');
  },
  data = [],
  containerStyle,
  border = false,
  ListFooterComponent,
  ListEmptyComponent,
}: GridViewProps<T>) => {
  const [displayColumn, setColumn] = useState(column);
  const width = useBreakpoint();

  useEffect(() => {
    setColumn(column);
  }, [column]);

  useEffect(() => {
    const getColumnCount = () => {
      if (responsive) {
        if (width.xxl) {
          return (
            responsive.xxl ||
            responsive.xl ||
            responsive.lg ||
            responsive.md ||
            responsive.sm ||
            responsive.xs ||
            column
          );
        }
        if (width.xl) {
          return (
            responsive.xl ||
            responsive.lg ||
            responsive.md ||
            responsive.sm ||
            responsive.xs ||
            column
          );
        }
        if (width.lg) {
          return (
            responsive.lg ||
            responsive.md ||
            responsive.sm ||
            responsive.xs ||
            column
          );
        }
        if (width.md) {
          return responsive.md || responsive.sm || responsive.xs || column;
        }
        if (width.sm) {
          return responsive.sm || responsive.xs || column;
        }
        if (width.xs) {
          return responsive.xs || column;
        }
      }
      return column;
    };
    setColumn(getColumnCount());
  }, [width, column, responsive]);

  const borderStyle = {
    border: `1px solid #DBDBDB`,
    backgroundColor: 'white',
    borderRadius: 4,
    overflow: 'hidden',
  };

  let style = containerStyle;
  if (border) {
    style = { ...style, ...borderStyle };
  }

  useBottomScrollListener(onEndReached, {
    offset: 200,
    debounce: 200,
    triggerOnNoScroll: true,
  });

  const gapWidth = itemPadding * (displayColumn - 1);
  const oneColumnGap = gapWidth / displayColumn;

  return (
    <StyledGridContainer
      style={{
        display: 'flex',
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: itemPadding,
        marginTop: 10,
        ...style,
      }}
    >
      {/*  <AppAnimateGroup
        enter={{
          animation,
        }}
        style={{
          display: 'flex',
          flexDirection: 'row',
          flexWrap: 'wrap',
          gap: itemPadding,
          marginTop: 10,
          ...style,
        }}
      >*/}
      {data?.length > 0
        ? data.map((item, index) => (
            <StyledGridColumnCount
              key={'grid-' + index}
              style={{
                flexGrow: 0,
                maxWidth: `calc(${100 / displayColumn}% - ${oneColumnGap}px)`,
                flexBasis: `calc(${100 / displayColumn}% - ${oneColumnGap}px)`,
                // padding: itemPadding,
                boxSizing: 'border-box',
              }}
            >
              {renderItem(item, index)}
            </StyledGridColumnCount>
          ))
        : null}
      {/*      </AppAnimateGroup>*/}
      {data?.length === 0 ? getEmptyContainer(ListEmptyComponent) : null}
      {getFooterContainer(ListFooterComponent)}
    </StyledGridContainer>
  );
};

export default GridView;
