'use client';
import styled from 'styled-components';
import { Layout } from 'antd';

export const StyledLayout = styled(Layout)`
  /*  height: 100vh;
  max-height: 100%;*/
  min-height: 100vh;
  // width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  background: linear-gradient(
    90deg,
    rgba(138, 119, 255, 0.14) 50%,
    rgba(245, 136, 255, 0.14) 100%
  );
`;
