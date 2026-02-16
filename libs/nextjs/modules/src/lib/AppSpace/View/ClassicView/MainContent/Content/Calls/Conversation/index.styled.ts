import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;

export const UserChatRow = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: flex-end;
  margin: 16px 0;
  gap: 8px;
  animation: slideInRight 0.3s ease-out;

  @keyframes slideInRight {
    from {
      opacity: 0;
      transform: translateX(20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    padding: 14px;
  }
`;

export const MessageWrapper = styled.div<{ $isUser?: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: ${({ $isUser }) => ($isUser ? 'flex-end' : 'flex-start')};
  max-width: 70%;

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    max-width: 83%;
  }
`;

export const MessageMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
  font-size: 11px;
  color: ${({ theme }) => theme.palette.text.secondary};
  opacity: 0.7;
`;

export const UserBubble = styled(Paragraph)`
  padding: 12px 16px;
  border-radius: 16px 16px 4px 16px;
  background-color: rgba(152, 128, 255, 0.1);
  color: ${({ theme }) => theme.palette.text.primary};
  margin: 0;
  word-wrap: break-word;
  line-height: 1.5;
  font-size: 14px;

  &.ant-typography {
    margin-bottom: 6px;
  }
`;

export const AssistantChatRow = styled.div`
  display: flex;
  justify-content: flex-start;
  align-items: flex-end;
  margin: 16px 0;
  gap: 8px;
  animation: slideInLeft 0.3s ease-out;

  @keyframes slideInLeft {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    padding: 14px;
  }
`;

export const AssistantBubble = styled(Paragraph)`
  padding: 12px 16px;
  border-radius: 16px 16px 16px 4px;
  background: ${({ theme }) => theme.palette.background.component};
  border: 1px solid
    ${({ theme }) => (theme as any).palette?.border || 'rgba(0, 0, 0, 0.06)'};
  margin: 0;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;

  &.ant-typography {
    margin-bottom: 6px;
  }

  code {
    background: ${({ theme }) => theme.palette.background.default};
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 13px;
  }

  pre {
    background: ${({ theme }) => theme.palette.background.default};
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 8px 0;
  }
`;

export const AvatarContainer = styled.div<{ $isUser?: boolean }>`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: ${({ $isUser, theme }) =>
    $isUser ? '#5071F6' : theme.palette.background.paper};
  border: 2px solid
    ${({ theme }) => (theme as any).palette?.border || 'rgba(0, 0, 0, 0.06)'};
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: ${({ $isUser, theme }) =>
    $isUser ? theme.palette.common.white : theme.palette.text.primary};
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);

  svg {
    width: 20px;
    height: 20px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    width: 25px;
    height: 25px;

    svg {
      width: 18px;
      height: 18px;
    }
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    display: none;
  }
`;
