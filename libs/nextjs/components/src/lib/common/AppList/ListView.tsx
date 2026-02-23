import React, {ReactNode} from 'react';
import {useBottomScrollListener} from 'react-bottom-scroll-listener';
import {Spin} from 'antd';
import {StyledContentWrapper, StyledListContainer, StyledLoadingOverlay, StyledScrollViewport,} from './index.styled';

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

type ListViewProps<T> = {
  renderItem: (item: T, index: number) => ReactNode;
  onEndReached?: () => void;
  data?: T[];
  ListFooterComponent?: ReactNode;
  ListEmptyComponent?: ReactNode;
  extra?: ReactNode;
  style?: React.CSSProperties;
  loading?: boolean;
  isLoadingMore?: boolean;
};

const ListView = <T, >({
                         renderItem,
                         onEndReached = () => {
                           console.log('defaultProps onEndReached');
                         },
                         data = [],
                         ListFooterComponent,
                         ListEmptyComponent,
                         extra,
                         ...rest
                       }: ListViewProps<T>) => {
  const containerRef = useBottomScrollListener<HTMLDivElement>(onEndReached, {
    offset: 200,
    debounce: 50,
    triggerOnNoScroll: false,
  });

  const {height, maxWidth, padding, ...otherStyles} = rest?.style || {};

  return (
    <StyledScrollViewport
      className="app-list"
      style={{height, ...otherStyles}}
      ref={containerRef}
    >
      {extra}
      <StyledContentWrapper $maxWidth={maxWidth} $padding={padding}>
        <StyledListContainer>
          {data?.length > 0 ? (
            <>
              {rest.loading && !rest.isLoadingMore && (
                <StyledLoadingOverlay>
                  <Spin/>
                </StyledLoadingOverlay>
              )}
              {data.map((item, index) => renderItem(item, index))}
              {getFooterContainer(ListFooterComponent)}
            </>
          ) : (
            getEmptyContainer(ListEmptyComponent)
          )}
        </StyledListContainer>
      </StyledContentWrapper>
    </StyledScrollViewport>
  );
};

export default ListView;
