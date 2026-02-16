'use client';
import React from 'react';
import styled from 'styled-components';
import { SignUpSkeleton } from '@unpod/skeleton/AuthLayout/SignupPage';

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
const AppLoader = () => {
  return (
    <StyledAppLoader>
      {/* <Spin /> */}
      <SignUpSkeleton />
    </StyledAppLoader>
  );
};

export default AppLoader;
