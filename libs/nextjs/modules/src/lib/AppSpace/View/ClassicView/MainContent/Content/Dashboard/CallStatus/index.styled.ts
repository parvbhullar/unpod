import styled from 'styled-components';
import {Card} from 'antd';

export const StyledCard = styled(Card)`
  //background-color: ${({theme}) => theme.palette.background.component};
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);

  .ant-card-body {
    @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
      padding: 12px !important;
    }
  }
`;

export const Container = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

export const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
`;

export const Title = styled.h2`
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #000000;
`;

export const TotalText = styled.span`
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 400;
`;

export const StatusList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

export const StatusItem = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    gap: 8px;
  }
`;

export const IconWrapper = styled.div<{ $bgColor?: string; $color?: string }>`
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background-color: ${(props) => props.$bgColor};
  color: ${(props) => props.$color};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    font-size: 14px;
    width: 40px;
    height: 40px;
  }
`;

export const StatusContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

export const StatusLabel = styled.div`
  font-size: 16px;
  color: #000000;

  @media (max-width: ${({theme}) => theme.breakpoints.xss}px) {
    font-size: 11px;
    white-space: nowrap;
    min-width: 50px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`;

export const ProgressWrapper = styled.div`
  width: 100%;

  .ant-progress-outer {
    padding-right: 0;
  }

  .ant-progress-inner {
    border-radius: 100px;
    background-color: #f0f0f0;
  }

  .ant-progress-bg {
    border-radius: 100px !important;
    height: 8px !important;
  }

  @media (min-width: ${({theme}) => theme.breakpoints.xs}) {
    width: 120px;
  }
`;

export const StatusStats = styled.div`
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-shrink: 0;
  min-width: 120px;
  justify-content: flex-end;

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    min-width: auto;
  }
`;

export const StatusCount = styled.span`
  font-size: 18px;
  font-weight: 600;
  color: #000000;

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    font-size: 14px;
    white-space: nowrap;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.xss}px) {
    font-size: 11px;
    white-space: nowrap;
  }
`;

export const StatusPercentage = styled.span`
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 400;

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    font-size: 11px;
    white-space: nowrap;
  }
`;
