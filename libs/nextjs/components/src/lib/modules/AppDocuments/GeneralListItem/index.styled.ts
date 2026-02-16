import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledRoot = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px 10px 10px 16px;
  border-block-end: 1px solid ${({ theme }) => theme.border.color};

  &:hover {
    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  }

  &.active,
  &.selected {
    background-color: ${({ theme }) => theme.palette.primaryHover};
    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
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
  margin-bottom: 3px;
`;

export const StyledMeta = styled(Typography.Paragraph)`
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 0 !important;

  & .ant-typography {
    margin-bottom: 0 !important;
  }
`;

export const StyledItem = styled.div`
  & .ant-avatar-string {
    font-size: 14px;
  }
`;

export const StyledHeaderExtra = styled.div`
  display: flex;
`;
