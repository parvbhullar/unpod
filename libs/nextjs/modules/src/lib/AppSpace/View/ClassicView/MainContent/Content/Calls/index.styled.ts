import styled, {keyframes} from 'styled-components';
import {Card, Typography} from 'antd';

const {Text, Title} = Typography;

const bounce = keyframes`
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
`;

export const StyledTypingLoader = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 24px;

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    height: 21px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    height: 18px;
  }
`;

export const StyledDot = styled.span`
  width: 6px;
  height: 6px;
  background-color: ${({theme}) => theme.palette.primary};
  border-radius: 50%;
  display: inline-block;
  animation: ${bounce} 1.4s infinite ease-in-out both;

  &:nth-child(1) {
    animation-delay: -0.32s;
  }

  &:nth-child(2) {
    animation-delay: -0.16s;
  }

  &:nth-child(3) {
    animation-delay: 0s;
  }
`;

export const StyledRoot = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  display: flex;
  flex-direction: column;
  height: calc(100vh - 76px);
`;

export const StyledMetricsContainer = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  border-bottom: ${({theme}) => theme.border.width}
    ${({theme}) => theme.border.style} ${({theme}) => theme.border.color};
  width: 100%;
`;

export const StyledAnalyticsCard = styled(Card)`
  background-color: ${({theme}) => theme.palette.background.default};
  box-shadow: ${({theme}) => theme.component.card.boxShadow};

  .ant-card-body {
    padding: 12px 24px !important;
    @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
      padding: 10px !important;
    }

    @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
      padding: 10px !important;
    }
  }
`;

export const StyledMetricsContent = styled.div`
  flex: 1;
  max-width: calc(${({theme}) => theme.sizes.mainContentWidth});
  display: flex;
  margin: 0 auto;
  justify-content: space-between;
  padding: 16px 32px;
  gap: 8px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 8px 10px;
  }
`;

export const StyledText = styled(Text)`
  text-transform: uppercase;
  font-size: 12px;
  text-align: center;

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    font-size: 11px !important;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    font-size: 8px !important;
  }
`;

export const StyledTitle = styled(Title)`
  text-align: center;
  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
  }
  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    font-size: 14px !important;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    font-size: 12px !important;
  }
`;

export const StyledTabsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  scrollbar-width: thin;

  .ant-tabs-nav-wrap {
    width: ${({theme}) => theme.sizes.mainContentWidth};
    max-width: 100%;
    margin: 0 auto !important;
    flex: none !important;

    @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
      max-width: 100% !important;
    }
  }

  .ant-tabs-nav {
    position: sticky;
    top: 0;
    background: ${({theme}) => theme.palette.background.default};
    z-index: 10;
  }

  .ant-tabs-content-holder {
    flex: 1;
    width: 100% !important;
  }

  .ant-tabs-top > .ant-tabs-nav {
    margin: 0 !important;
  }

  .ant-tabs-nav {
    padding: 0 14px;
  }
`;
