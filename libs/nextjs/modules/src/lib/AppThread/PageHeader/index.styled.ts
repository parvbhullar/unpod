import styled from 'styled-components';
import { Button, Typography } from 'antd';

export const StyledButton = styled(Button)`
  display: flex;
  align-items: center;
  padding: 4px 15px !important;
  height: 36px !important;
`;

export const StyledTitleBlock = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 16px;
`;

export const StyledMainTitle = styled(Typography.Paragraph)`
  font-size: 18px !important;
  font-weight: 600 !important;
  margin-bottom: 0 !important;
`;

export const StyledTitleWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
`;
