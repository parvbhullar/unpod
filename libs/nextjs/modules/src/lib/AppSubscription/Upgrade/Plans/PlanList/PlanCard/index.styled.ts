import styled from 'styled-components';
import { Badge } from 'antd';

export const StyledBadge = styled(Badge)<{ $variant?: string }>`
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: ${({ $variant }) => {
    if ($variant === 'default')
      return 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)';
    if ($variant === 'popular')
      return 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)';
    return '#c4b5fd';
  }};
  color: ${({ $variant }) =>
    $variant === 'default' || $variant === 'popular' ? '#ffffff' : '#5b21b6'};
  font-size: 11px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 1;

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;

    @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      max-width: 300px;
    }

    @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
      max-width: 250px;
    }
  }
`;

export const StyledContainer = styled.div`
  padding: 20px;
  border: 1px solid ${({ theme }) => theme.border.color};
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  transition: border-color 0.3s;

  &.active {
    // background-color: ${({ theme }) => theme.palette.primaryActive};
    border-color: ${({ theme }) => theme.palette.primary};
  }

  &:hover {
    border-color: ${({ theme }) => theme.palette.primary};
  }
`;

export const StyledRow = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;

  & .strike {
    text-decoration: line-through;
  }
`;

export const StyledIdealFor = styled.p`
  font-size: 13px;
  color: ${({ theme }) => theme.palette.text.secondary};
  text-align: center;
  margin-top: auto;
  margin-bottom: 8px;
  font-style: italic;
  padding-top: 12px;
`;

export const StyledButtonContainer = styled.div<{ $isHelpText?: boolean }>`
  margin-top: ${({ $isHelpText }) => ($isHelpText ? 0 : 'auto')};
  padding-top: 0;
`;

export const StyledListContainer = styled.div`
  margin-inline: 4px;
`;

export const StyledHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;

  & .ant-typography {
    margin-bottom: 0;
  }
`;

export const StyledFeatureItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  &:last-child {
    margin-bottom: 0;
  }
`;
