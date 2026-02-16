import { Card, List } from 'antd';
import styled from 'styled-components';

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  height: calc(100vh - 130px);
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledDocumentsList = styled.div`
  padding: 16px 32px;
  width: 100%;
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth});
  background-color: ${({ theme }) => theme.palette.background.default};
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 8px 10px;
  }
`;

export const StyledListItem = styled(List.Item)<{ $radius?: string }>`
  display: flex !important;
  align-items: center !important;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: ${({ theme, $radius }) =>
    $radius ? $radius : theme.radius.base}px !important;
  padding: 16px !important;
  gap: 8px;
  border: 1px solid ${({ theme }) => theme.border.color} !important;
  margin-bottom: 12px;
  background: ${({ theme }) => theme.palette.background.default};

  &:hover {
    background-color: ${({ theme }) => theme.palette.primaryHover} !important;
  }

  .ant-list-item-meta {
    align-items: center !important;
  }

  .ant-list-item-meta-avatar {
    margin-inline-end: 16px !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      margin-inline-end: 5px !important;
    }
  }

  .ant-list-item-meta-title {
    line-height: 1.5 !important;
    margin-bottom: 0 !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      font-size: 12px !important;
      line-height: 1.2 !important;
    }
  }

  .ant-list-item-meta-description {
    margin-top: 0 !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
    color: ${({ theme }) => theme.palette.text.secondary} !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      font-size: 10px !important;
      line-height: 1.2 !important;
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 6px 4px !important;
  }
`;

export const StyledListMeta = styled(List.Item.Meta)`
  &.ContentStart {
    align-items: flex-start !important;
  }
`;

export const StyledCard = styled(Card)`
  background-color: ${({ theme }) => theme.palette.background.component};
`;
