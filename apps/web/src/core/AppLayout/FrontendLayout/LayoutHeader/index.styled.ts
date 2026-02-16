import styled from 'styled-components';
import { Button, Layout } from 'antd';

const { Header } = Layout;

export const StyledHeader = styled(Header)<{ $headerBg?: string }>`
  display: flex;
  min-width: 0;
  flex-direction: column;
  // border-bottom: solid 1px #ccc;
  justify-content: center;
  line-height: 1;
  background: ${({ $headerBg }) =>
    $headerBg
      ? $headerBg
      : `linear-gradient(
          248.95deg,
          #f2eeff 3.95%,
          #ffeffd 38.71%,
          #f2eeff 70.73%,
          #ffeffd 106%
        )`} !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    padding-inline: 30px;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 14px;
  }
`;

export const StyledHeaderContainer = styled.div`
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
`;

export const StyledLogo = styled.div`
  font-weight: bold;
  font-size: 20px;
  color: ${({ theme }) => theme.palette.primary};

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 108px;
  }
`;

export const StyledMenu = styled.ul`
  display: flex;
  min-width: 0;
  margin: 0;
  list-style: none;
  padding: 0;
  line-height: 32px;

  & > li {
    padding-inline: 16px;

    & > a {
      color: ${({ theme }) => theme.palette.text.primary};
      &:hover {
        color: ${({ theme }) => theme.palette.primary};
      }
    }
  }
`;

export const StyledButton = styled(Button)`
  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
  border: none; /* remove default AntD border */
  color: white; /* make text visible */
  font-weight: 500;

  &:hover,
  &:focus {
    background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
    color: #ddd !important;
  }

  &.ant-btn.ant-btn-sm {
    font-size: 10px;
  }
`;
export const StyledJoinDiscordButton = styled(Button)`
  background-color: #f5f5f5ff;
  border-color: #f5f5f5;
  color: #000 !important;
  padding: 0 14px;

  &:hover,
  &:focus {
    background-color: #ececec !important;
    border-color: #b8b1b1ff !important;
    color: #000 !important;
  }
`;

export const StyledIconButton = styled(Button)`
  background: transparent !important;
  border: none !important;
  color: ${({ theme }) => theme.palette.text.primary} !important;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;

  &:hover,
  &:focus {
    background: rgba(0, 0, 0, 0.04) !important;
    color: ${({ theme }) => theme.palette.primary} !important;
  }
`;
