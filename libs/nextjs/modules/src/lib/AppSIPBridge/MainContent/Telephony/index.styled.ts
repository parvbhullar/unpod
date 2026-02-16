import styled from 'styled-components';
import { Typography } from 'antd';

const { Title } = Typography;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
`;

export const StyledMainInfo = styled.div`
  margin: 0;
`;

export const StyledHeading = styled(Title)`
  font-size: 28px;
`;

export const StyledActions = styled.div`
  display: flex;
  gap: 16px;
`;
export const StyledResponsiveText = styled.p`
  @media (max-width: 1020px) and (min-width: 328px) {
    display: none;
  }
`;

export const StyledListContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

export const StyledDrawerRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
`;

export const StyledProviderRoot = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: 32px;
  padding: 4px 10px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    gap: 10px;
    padding: 0;
    border: none;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    gap: 10px;
    padding: 4px 8px;
    height: 32px !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 52}px) {
    gap: 10px;
    padding: 4px 8px;
  }
`;

export const StyleProviderContent = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  @media (max-width: 768px) {
    display: none;
  }
`;

export const StyledIconWrapper = styled.div`
  background: ${({ theme }) => theme.palette.background.component};
  border-radius: 16px;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;
