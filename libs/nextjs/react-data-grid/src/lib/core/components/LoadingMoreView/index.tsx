import React from 'react';
import {Spin} from 'antd';
import styled from 'styled-components';

const StyledContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  background: #eae6ff;
  border-radius: 24px;
  transition: background 0.3s;
`;

const StyledRoot = styled.div`
  display: flex;
  justify-content: center;
  position: absolute;
  top: auto;
  bottom: 40px;
  right: 0;
  left: 0;
  z-index: 999900009;

  &:hover ${StyledContainer} {
    background: #d8d1ff;
  }
`;

type AppLoaderProps = {
  content?: React.ReactNode;
  position?: 'fixed' | 'absolute' | 'relative' | 'static';
  style?: React.CSSProperties;
};

export const LoadingMoreView = ({
                                  content = 'Loading more...',
                                  position = 'fixed',
                                  style,
                                  ...restProps
                                }: AppLoaderProps) => {
  return (
    <StyledRoot
      role="progress-loader"
      style={{position, ...style}}
      {...restProps}
    >
      <StyledContainer>
        <span role="spin">
          <Spin/>
        </span>
        {content}
      </StyledContainer>
    </StyledRoot>
  );
};

export default LoadingMoreView;
