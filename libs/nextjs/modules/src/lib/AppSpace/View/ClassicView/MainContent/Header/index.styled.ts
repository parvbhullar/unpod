import { Avatar, Typography } from 'antd';
import styled from 'styled-components';

const { Title, Text } = Typography;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.palette.background.default};
`;

export const IconWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 12px;

  svg {
    font-size: 24px;
  }

  & .ant-typography {
    margin: 0 !important;
  }
`;

export const StyledMainHeader = styled.div`
  padding: 12px 14px !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: ${({ theme }) => theme.palette.background.header};
  border-bottom: 1px solid ${({ theme }) => theme.border.color};
  height: 64px !important;
`;

export const StyledMainHeaderContent = styled.div`
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;
`;

export const StyledHeaderActions = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;

  @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
    gap: 6px;
  }
`;

export const StyledHeaderTitle = styled(Title)`
  font-size: 16px !important;
  font-weight: ${({ theme }) => theme.font.weight.medium} !important;
  margin: 0 !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  max-width: 100%;

  & > * {
    flex-shrink: 0;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    max-width: 190px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
    font-size: 12px !important;
    max-width: 135px;
  }
`;

export const StyledHeaderIcon = styled(Avatar)`
  background: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  flex-shrink: 0;
  text-transform: uppercase;
  transition: opacity 0.2s;
  border-radius: ${({ theme }) => theme.radius.base - 5}px !important;
  font-size: 14px !important;

  & > * {
    flex-shrink: 0;
  }

  &:hover {
    opacity: 0.9;
  }
`;

export const StyledHeaderSubtitle = styled(Text)`
  font-size: 12px;
  color: ${({ theme }) => theme.palette.text.secondary};
  margin: 0;
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 10px !important;
    max-width: 200px;
  }
`;

export const StyledCallTypeTag = styled(Typography.Text)`
  padding: 5px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #fff7e6;
  color: #fa8c16;
  text-transform: capitalize;

  &.inbound {
    background: #e6f7ff;
    color: #1890ff;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    border-radius: 50px !important;
    padding: 7px !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xss}px) {
    display: none;
  }
`;

type StatusTagProps = { $bg: string; $color: string };

export const StyledStatusTag = styled(Text)<StatusTagProps>`
  font-size: 12px;
  font-weight: 500;
  padding: 5px 12px;
  border-radius: 12px;
  text-transform: capitalize;

  display: inline-flex;
  align-items: center;
  gap: 6px;

  background-color: ${({ $bg }) => $bg};
  color: ${({ $color }) => $color};

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    border-radius: 50px !important;
    padding: 9px !important;
  }
`;
