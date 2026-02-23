import React from 'react';

import {StyledContainer, StyledInnerContainer} from './index.styled';

type AppPageContainerProps = {
  style?: React.CSSProperties;
  children?: React.ReactNode;
  [key: string]: unknown;
};

const AppPageContainer: React.FC<AppPageContainerProps> = ({
                                                             style,
                                                             ...props
                                                           }) => {
  return (
    <StyledContainer
      style={{
        /*display: 'flex',
        flexDirection: 'column',
        flex: 1,
        width: '100%',
        height: '100%',
        borderRadius: '10px 10px 0 0',
        backgroundColor: 'white',*/
        // width: 'calc(100% - 144px)',
        // marginInline: 72,
        ...style,
      }}
      {...props}
    >
      {/*{props.children}*/}

      <StyledInnerContainer>{props.children}</StyledInnerContainer>
    </StyledContainer>
  );
};

export default AppPageContainer;
