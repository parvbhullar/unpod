import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;

export const StyledRoot = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px 10px 10px 16px;

  &:hover {
    background-color: ${({ theme }) => theme.palette.primaryHover};
  }

  &.active,
  &.selected {
    background-color: ${({ theme }) => theme.palette.primaryHover};
  }
`;

export const StyledInnerRoot = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
`;

export const StyledListHeader = styled.div`
  display: flex;
  gap: 20px;
  align-self: stretch;
  justify-content: space-between;
`;

export const StyledMeta = styled(Typography.Paragraph)`
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 6px !important;

  & .ant-typography {
    margin-bottom: 0 !important;
    font-size: 14px !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-bottom: 3px !important;
  }
`;

export const StyledItem = styled.div`
  & .ant-avatar-string {
    font-size: 14px;
  }
`;

export const StyledHeaderExtra = styled.div`
  display: flex;

  & .ant-typography {
    font-size: 11px !important;
  }
`;

export const StyledParagraph = styled(Paragraph)`
  font-size: 12px !important;
  max-width: 90% !important;
`;
