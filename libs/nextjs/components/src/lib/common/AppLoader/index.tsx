import React from 'react';
import {Spin} from 'antd';
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
  style?: React.CSSProperties;
  position?: 'fixed' | 'absolute' | 'relative' | 'static';
};

const AppLoader: React.FC<AppLoaderProps> = ({
                                               position = 'fixed',
                                               style,
                                               ...restProps
                                             }) => {
  return (
    <StyledAppLoader style={{position, ...style}} {...restProps}>
      <Spin/>
    </StyledAppLoader>
  );
};

export default AppLoader;
