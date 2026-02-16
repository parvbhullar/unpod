import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledHeaderWrapper = styled.div`
  font-weight: bold;
  font-size: 16;
`;

export const StyledTitle = styled(Typography.Title).attrs({
  level: 1,
})`
  margin: 0 !important;
`;

export const StyledSubtext = styled(Typography.Text)`
  margin: 8px 0 0 0 !important;
  display: block !important;
`;

export const StyledRequiredDocsTitle = styled(Typography.Title).attrs({
  level: 4,
})`
  margin: 32px 0 16px 0 !important;
`;

export const StyledParagraph = styled(Typography.Paragraph)`
  margin: 0 !important;
`;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  align-items: flex-start;
`;
