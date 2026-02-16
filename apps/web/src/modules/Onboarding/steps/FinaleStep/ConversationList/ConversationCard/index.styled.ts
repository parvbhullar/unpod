import styled from 'styled-components';
import { Button, Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

export const CardWrapper = styled(Card)`
  border-radius: 8px;
  margin-bottom: 24px;
  width: 100%;
  background: ${({ theme }) => theme.palette.background.default};
  border: 1px solid ${({ theme }) => theme.border.color};

  .ant-card-body {
    padding: 16px !important;
  }

  .ant-card-meta-detail > div:not(:last-child) {
    margin-bottom: 2px !important;
  }
`;

export const StyledGridContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

export const StyledDescription = styled(Paragraph)`
  margin-top: 4px !important;
  margin-bottom: 4px !important;
  padding-left: 3px !important;
`;

export const StyledPrimaryButton = styled(Button)`
  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
  color: ${({ theme }) => theme.palette.common.white} !important;
  font-weight: ${({ theme }) => theme.font.weight.medium} !important;
  font-size: ${({ theme }) => theme.font.size.base} !important;
  padding: 8px 16px !important;
  margin-top: 8px !important;

  &:hover {
    background: linear-gradient(90deg, #a839ff 0%, #377dff 100%) !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    padding: 14px 32px !important;
    height: 42px !important;
    max-width: 250px !important;
  }
`;

export const StyledSectionLabel = styled(Title)`
  font-size: 18px !important;
  font-weight: 600;
  margin: 0 !important;
`;

export const StyledButtonWrapper = styled.div`
  display: flex;
  margin: auto !important;
`;
