import React, { ReactNode, useEffect } from 'react';
import { Menu, Spin, Typography } from 'antd';
import { useBottomScrollListener } from 'react-bottom-scroll-listener';
import {
  StyledMenuContainer,
  StyledOverlayLoader,
  StyledOverlayLoaderText,
} from './index.styled';
import { SidebarAgentList } from '@unpod/skeleton';
import type { MenuProps } from 'antd/es/menu';

const { Text } = Typography;

type AppMenuProps = {
  loading?: boolean;
  initialLoader?: ReactNode;
  items?: MenuProps['items'];
  onSelect?: MenuProps['onSelect'];
  noDataMessage?: string;
  onEndReached?: () => void;
  selectedKeys?: string[];};

const AppMenu: React.FC<AppMenuProps> = ({
  loading = false,
  initialLoader = <SidebarAgentList />,
  items = [],
  onSelect,
  noDataMessage,
  onEndReached,
  selectedKeys,
}) => {
  const containerRef = onEndReached
    ? useBottomScrollListener<HTMLDivElement>(onEndReached, {
        offset: 200,
        debounce: 200,
        triggerOnNoScroll: false,
      })
    : null;

  useEffect(() => {
    const container = containerRef?.current;

    if (
      container &&
      container.scrollHeight <= container.clientHeight &&
      items.length === 10 &&
      onEndReached
    ) {
      onEndReached();
    }
  }, [items.length, onEndReached]);

  return (
    <StyledMenuContainer ref={items.length > 0 ? containerRef : null}>
      <Menu
        mode="inline"
        items={items}
        selectedKeys={selectedKeys}
        onSelect={onSelect}
      />

      {items.length === 0 && !loading && (
        <StyledOverlayLoader>
          <StyledOverlayLoaderText>
            <Text type="secondary">{noDataMessage || 'No records found'}</Text>
          </StyledOverlayLoaderText>
        </StyledOverlayLoader>
      )}

      {items.length === 0 && loading && initialLoader}

      {loading && items.length > 0 && (
        <StyledOverlayLoader>
          <StyledOverlayLoaderText>
            <Spin size="small" />
            <Text type="secondary">Loading...</Text>
          </StyledOverlayLoaderText>
        </StyledOverlayLoader>
      )}
    </StyledMenuContainer>
  );
};

export default AppMenu;
