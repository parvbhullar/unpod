import React from 'react';
import styled from 'styled-components';

type StyledFormBodyProps = {
  $bodyHeight?: number;
  $overFlowY?: React.CSSProperties['overflowY'];
  $paddingRight?: boolean;
};

const StyledFormBody = styled.div<StyledFormBodyProps>`
  height: ${({ $bodyHeight }) =>
    `calc(100vh - ${$bodyHeight ? $bodyHeight : 152}px)`};
  overflow-y: ${({ $overFlowY }) => ($overFlowY ? $overFlowY : 'auto')};
  scrollbar-width: thin;
  padding-right: ${({ $paddingRight }) => ($paddingRight ? '16px' : '0')};
`;

const StyledInnerBody = styled.div`
  padding-top: 5px;
  overflow: hidden;
`;

type DrawerBodyProps = {
  bodyHeight?: number;
  overFlowY?: React.CSSProperties['overflowY'];
  isTabDrawer?: boolean;
  children?: React.ReactNode;
  [key: string]: unknown;
};

export const DrawerBody = ({
  bodyHeight,
  overFlowY,
  isTabDrawer,
  children,
  ...restProps
}: DrawerBodyProps) => {
  return (
    <StyledFormBody
      $bodyHeight={bodyHeight}
      $overFlowY={overFlowY}
      $paddingRight={isTabDrawer}
    >
      <StyledInnerBody {...restProps}>{children}</StyledInnerBody>
    </StyledFormBody>
  );
};

export default React.memo(DrawerBody);
