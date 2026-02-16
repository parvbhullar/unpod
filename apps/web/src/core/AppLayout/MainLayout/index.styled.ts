'use client';
import styled from 'styled-components';
import { Layout } from 'antd';

const { Content } = Layout;

export const StyledLayout = styled(Layout)`
  display: flex;
  flex-direction: column;
  min-width: 0;
  width: 100%;
  position: relative;
  background-color: ${({ theme }) => theme.palette.background.default};
  min-height: 100vh;
`;

export const StyledMain = styled(Layout)`
  /*background: linear-gradient(
    90deg,
    rgba(138, 119, 255, 0.14) 50%,
    rgba(245, 136, 255, 0.14) 100%
  );*/
  background-color: ${({ theme }) => theme.palette.background.default};
`;

export const StyledContent = styled(Content)`
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  width: 100%;
  justify-content: center;
  align-items: center;
  margin: 0 auto;
  // height: 100vh;
  // overflow: hidden;
`;

export const StyledLayoutMain = styled.div`
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  flex: 1;
  margin-inline-start: 72px;
  width: calc(100% - 72px);

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-inline-start: 60px;
    width: calc(100% - 60px);
  }
`;
