import styled from 'styled-components';
import { Button, Typography } from 'antd';

const { Title } = Typography;

export const StyledTitleContainer = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;

  @media (max-width: 768px) {
    & .ant-flex-gap-small {
    }

    width: 90%;
  }
`;

export const StyledTitleWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: 20px;

  & .ant-form-item {
    margin-bottom: 2px !important;
  }

  @media (max-width: 768px) {
    flex-wrap: wrap;
    margin-right: 0;
    gap: 6px;
  }
`;

export const TitleWrapper = styled.div`
  width: 100%;
  max-width: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    max-width: 180px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl + 168}px) {
    max-width: 280px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 52}px) {
    max-width: 190px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    max-width: 170px !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
    max-width: 130px !important;
  }
`;

export const StyledTitle = styled(Title)`
  margin-bottom: 0 !important;
  flex: 1;
  font-weight: bold;
  padding: 4px 11px;
  border: 1px solid transparent;
  font-size: 20px;

  &.ant-typography-edit-content {
    inset-inline-start: -11px !important;
    margin-top: 0 !important;
    padding: 0 11px;
    border: 0 none;
  }

  & .ant-input-outlined {
    outline: none;
    box-shadow: none;
    width: 20%;
  }

  @media (max-width: 796px) {
    white-space: nowrap;
    overflow: hidden;

    font-size: 17px !important;
    padding: 2px 8px;
  }

  @media (max-width: 480px) {
    font-size: 14px;
  }
`;

export const StyledAgentInput = styled.div`
  border: 0 none;
  padding: 4px 6px;
  cursor: pointer;
  height: 28px;
  gap: 8px;
  display: flex;
  align-items: center;
  border-radius: 6px;
  width: 240px;

  &:hover {
    background: ${({ theme }) => theme.palette.background.component};
  }

  .ant-typography {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 230px !important;
    display: block;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 180px;
    .ant-typography {
      max-width: 170px !important;
    }
  }
`;

export const StyledDescContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;

  & .ant-typography {
    flex: 1;
    padding: 8px 11px;
    border: 1px solid transparent;
    border-radius: ${({ theme }) => theme.radius.base}px;
    background-color: ${({ theme }) => theme.palette.background.component};

    &:hover {
      border-color: ${({ theme }) => theme.border.color};
    }

    &.ant-typography-edit-content {
      inset-inline-start: 0 !important;
      margin-top: 0 !important;
      padding: 0;
      border: 0 none;

      & .ant-input {
        padding: 8px 11px;
      }
    }
  }
`;

export const StyledActionIcon = styled.div`
  display: flex;
  // align-items: center;
  justify-content: center;
  cursor: pointer;
  color: ${({ theme }) => theme.palette.success};
  padding: 5px;
  border-radius: ${({ theme }) => theme.radius.base}px;

  &.close-btn {
    color: ${({ theme }) => theme.palette.error};
  }

  &:hover {
    background-color: ${({ theme }) => theme.palette.background.component};
  }

  @media (max-width: 480px) {
    padding: 3px;
  }
`;

export const StyledIconWrapper = styled.div`
  color: ${({ theme }) => theme.palette.primary};
  font-size: 18px;
  padding-top: 4px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
  }
`;
export const StyledAppInputWrapper = styled.div`
  width: 100%;
  background: #f9f9f9;
  border: 0 none;
  padding: 6px 12px;
  cursor: pointer;
  height: 36px;
  gap: 8px;
  display: flex;
  max-width: fit-content;
  justify-content: space-between;
  align-items: center;

  font-size: 14px;
  & .ant-typography {
    width: fit-content;
  }
  @media (max-width: 768px) {
    & .ant-typography {
      width: fit-content;
      max-width: 70%;
      overflow: hidden;
    }
    white-space: nowrap;
    font-size: 13px;
    text-overflow: ellipsis;
  }
`;

// Add this styled component for responsive slug/copy are
export const StyledSlugWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;

  .slug-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: fit-content;
    font-size: 14px;
    color: #888;
    vertical-align: middle;
    @media (max-width: 768px) {
      font-size: 13px;
    }
  }
`;

export const StyledContainer = styled.div`
  padding: 13px;
`;

export const StyledEditButton = styled(Button)`
  height: 36px;
  width: 40px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: 28px !important;
    width: 28px !important;
  }
`;
