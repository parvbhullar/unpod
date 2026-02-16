import styled from 'styled-components';
import { Row } from 'antd';

export const StyledRoot = styled.div`
  flex: 1;
  height: calc(100vh - 74px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
`;

export const StyledContainer = styled.div`
  flex: 1;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 16px auto 16px;
  //padding-inline: 16px;
  display: flex;
  flex-direction: column;
  gap: 40px;
  align-items: center;
  justify-content: center;
  padding: 0 14px !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg + 200}px) {
    width: 500px;
  }
`;

export const StyledAskContainer = styled.div`
  margin: 8px auto 8px;
  width: 100%;
  max-width: 640px;
  //display: flex;
  //flex-direction: column;
  align-items: center;
  justify-content: center;
  transition:
    min-height 0.8s,
    margin 0.8s;
  border: 2px solid rgba(155, 143, 255, 0.3);
  border-radius: 16px;
  background: linear-gradient(
    135deg,
    rgba(240, 240, 255, 0.05) 0%,
    rgba(232, 228, 255, 0.05) 50%,
    rgba(222, 216, 255, 0.05) 100%
  );

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin-top: 0;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
    padding: 0 12px;
  }
`;

export const StyledInfoContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  text-align: center;

  & .ant-typography {
    margin: 0 !important;
  }
`;

export const StyledRow = styled(Row)`
  padding: 16px;
  min-height: 80%;
`;

export const StyledSegmentWrapper = styled.div`
  width: 100%;
`;

export const StyledSegmented = styled.div`
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth});
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin: 0 auto;
`;
