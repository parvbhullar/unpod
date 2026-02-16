import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledContainer = styled.div<{ $isScrolled?: boolean }>`
  margin: ${({ $isScrolled }) =>
    $isScrolled ? '16px auto 16px' : '16px auto 240px'};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  /*min-height: ${({ $isScrolled }) =>
    $isScrolled ? '50vh' : 'calc(100vh - 300px)'};*/
  min-height: ${({ $isScrolled }) =>
    $isScrolled ? 'calc(100vh - 100px)' : 'calc(100vh - 100px)'};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition:
    min-height 0.8s,
    margin 0.8s;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin-top: 0;
    min-height: ${({ $isScrolled }) =>
      $isScrolled ? '50vh' : 'calc(100vh - 184px)'};
  }
`;

export const StyledInfoContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 30px;
  text-align: center;

  & .ant-typography {
    margin: 0 !important;
  }
`;

export const StyledTabButtons = styled.div`
  display: flex;
  justify-content: center;
  gap: 16px;
  position: sticky;
  top: 12px;
  z-index: 101;
  max-width: 230px;
  margin: 24px auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    z-index: 0;
  }
`;

export const StyledTabContent = styled.div`
  opacity: 0;
  height: 0;
  width: 0;
  overflow: hidden;
  margin-bottom: 0;
  transition: all 0.3s ease;

  &.active {
    opacity: 1;
    height: auto;
    width: auto;
    margin-bottom: 16px;
    min-height: 360px;
  }
`;

export const StyledSpaceContainer = styled.div`
  flex: 1;
  margin: 0 auto;
  //padding: 24px;
  //background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  width: 1050px;
  max-width: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
    padding: 10px;
  }
`;

export const StyledTitle = styled(Typography.Paragraph)`
  font-size: 48px !important;
  font-weight: 700 !important;
  margin-bottom: 12px !important;
  text-align: center;
  color: ${({ theme }) => theme.palette.primary} !important;
  font-family: 'Berkshire Swash', cursive;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 42px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 38px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 34px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 28px !important;
  }
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
  min-height: 50vh;
`;

export const StyledNoAccessText = styled(Typography.Title)`
  text-align: center;
`;

export const StyledSettingContainer = styled.div`
  position: relative;
  padding: 8px 16px 16px 16px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 16px auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin: 0 auto;
  }
`;
