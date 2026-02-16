import React from 'react';
import { Spin } from 'antd';
import styled from 'styled-components';

const StyledAppLoader = styled.div`
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  flex: 1;
  background-color: #c6c6c633;
  align-items: center;
  z-index: 999900009;
  justify-content: center;
  min-height: 100%;
`;

type AppLoaderProps = {
  position?: 'fixed' | 'absolute' | 'relative' | 'static';
  style?: React.CSSProperties;
};

export const LoadingView = ({
  position = 'fixed',
  style,
  ...restProps
}: AppLoaderProps) => {
  return (
    <StyledAppLoader
      role="progress-loader"
      style={{ position, ...style }}
      {...restProps}
    >
      <span role="spin">
        <Spin />
      </span>
    </StyledAppLoader>
  );
};

export default LoadingView;
