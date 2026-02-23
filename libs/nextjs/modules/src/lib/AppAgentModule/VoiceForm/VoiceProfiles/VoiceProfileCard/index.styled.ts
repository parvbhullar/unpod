import styled from 'styled-components';
import {Button, Typography} from 'antd';

const {Text} = Typography;

export const StyledButton = styled(Button)`
  position: absolute;
  top: -7px;
  right: -6px;
  display: none;
  width: 20px !important;
  height: 20px !important;
`;

export const StyledCard = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
  padding: 14px 24px;
  background: ${({theme}) => theme.palette.background.default};
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid ${(props) => props.theme.border.color};
  border-radius: 12px;

  &:hover,
  &.selected {
    border-color: ${(props) => props.theme.palette.primary};

    ${StyledButton} {
      display: block;
    }

    .profile-name {
      color: ${({theme}) => theme.palette.primary || '#796cff'};
    }
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    gap: 12px;
    padding: 12px 20px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 12px 16px;
    gap: 10px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    padding: 10px 12px;
  }
`;

export const StyledProfileContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
`;

export const StyledProfileMain = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

export const StyledMetricsRow = styled.div`
  display: flex;
  gap: 20px;
`;

export const StyledMetric = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
`;

export const StyledMetricBarContainer = styled.div`
  width: 40px;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
`;

export const StyledMetricBar = styled.div`
  height: 100%;
  border-radius: 2px;
`;

export const StyledText = styled(Text)`
  min-width: 70px;
  color: #1a1d24;
`;

export const StyledLanguageTag = styled.span`
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  background: #f0f9ff;
  color: #0284c7;
  border-radius: 4px;
  border: 1px solid #bae6fd;
  cursor: pointer;
`;

export const StyledProviderTag = styled.span`
  font-size: 10px;
  font-weight: 500;
  padding: 2px 7px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
`;

export const StyledCostLabel = styled(Text)`
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    font-size: 9px;
  }
`;

export const StyledValueTag = styled(Text)`
  font-size: 11px;
  color: #374151;
  font-weight: 500;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    font-size: 10px;
  }
`;

export const PlayButton = styled(Button)<{
  borderColor: string;
  primaryColor: string;
  isPlaying?: boolean;
  isSelected?: boolean;
}>`
  width: 36px !important;
  height: 36px;
  min-width: 36px !important;
  border: 1.5px solid ${({borderColor}) => borderColor};
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: ${({isPlaying, isSelected, primaryColor}) =>
  isPlaying || isSelected ? primaryColor : 'inherit'};

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    width: 32px !important;
    height: 32px;
    min-width: 32px !important;
  }
`;
