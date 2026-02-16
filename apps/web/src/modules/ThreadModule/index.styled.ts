import styled from 'styled-components';
import { Button, Row } from 'antd';

export const StyledRoot = styled.div`
  height: 100%;
  width: 100%;
`;

export const StyledThreadContainer = styled.div`
  position: relative;
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
`;

export const StyledContainer = styled.div`
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  width: 100%;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: 12px 12px 0 0;
`;

export const StyledDetailsRoot = styled.div`
  width: calc(${({ theme }) => theme.sizes.mainContentWidth} + 128px);
  background-color: ${({ theme }) => theme.palette.background.default};
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;
  // gap: 40px;

  // height: calc(100vh - 129px);
  /*height: calc(100vh - 64px);

  & .simplebar-content {
    min-height: calc(100vh - 64px);
    display: flex;
    flex-direction: column;
  }*/
`;

export const StyledRow = styled(Row)`
  padding: 16px;
`;

export const StyledPostButton = styled(Button)`
  padding: 4px 15px !important;
  height: 36px !important;
`;

export const StyledMoreContainer = styled.div`
  display: flex;
  justify-content: center;
  padding-top: 24px;
`;

export const StyledNoAccessContainer = styled.div`
  margin: 16px auto;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
`;
