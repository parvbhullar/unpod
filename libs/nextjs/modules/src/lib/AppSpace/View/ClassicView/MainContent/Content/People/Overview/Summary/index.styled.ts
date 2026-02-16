import styled from 'styled-components';
import { Card, Typography } from 'antd';

const { Text } = Typography;

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 32px;
`;

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
`;

export const StyledDateHeader = styled(Text)`
  font-size: 16px;
`;

export const StyledCard = styled(Card)`
  background-color: ${({ theme }) => theme.palette.background.component};

  .ant-card-body {
    padding: 12px !important;
  }
`;

export const StyledAnalyticsCard = styled(Card)`
  background-color: ${({ theme }) => theme.palette.background.default};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};

  .ant-card-body {
    padding: 12px !important;
  }
`;

export const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
`;

export const StyledCardTitle = styled(Text)`
  font-size: 12px !important;
`;
