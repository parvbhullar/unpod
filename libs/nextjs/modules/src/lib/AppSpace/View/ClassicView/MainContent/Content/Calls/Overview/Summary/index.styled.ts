import styled from 'styled-components';
import { Card, Flex, Typography } from 'antd';

const { Text } = Typography;

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 24px 8px;

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    padding: 24px 14px;
  }
`;

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  margin: 0 auto;
`;

export const StyledPageHeader = styled(Flex)`
  svg {
    font-size: 20px;
    color: ${({ theme }) => theme.palette.text.secondary};
  }
`;

export const StyledSummarySection = styled.div`
  margin-top: 8px;
`;

export const StyledSummaryHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;

  svg {
    font-size: 20px;
    color: ${({ theme }) => theme.palette.text.secondary};
  }

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: ${({ theme }) => theme.palette.text.primary};
  }
`;

export const StyledSummaryCard = styled(Card)`
  background-color: ${({ theme }) => theme.palette.background.paper};
  border-radius: 12px;
  border: 1px solid ${({ theme }) => theme.border.color};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .ant-card-body {
    padding: 24px;
  }

  .markdown-viewer {
    color: ${({ theme }) => theme.palette.text.primary};
    line-height: 1.6;
    font-size: 14px;

    h1,
    h2,
    h3 {
      color: ${({ theme }) => theme.palette.text.primary};
      margin-top: 1.2em;
      margin-bottom: 0.5em;
    }

    p {
      margin-bottom: 0.8em;
    }

    strong {
      font-weight: 600;
    }
  }
`;

export const StyledLabel = styled(Text)`
  font-size: 14px;
  font-weight: 600;
`;
