import React from 'react';
import styled from 'styled-components';

const ChatMessageContainer = styled.div<{ $hideName: boolean }>`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-top: ${({$hideName}) => ($hideName ? '0' : '1.5rem')};
`;

const NameContainer = styled.div<{ $isSelf: boolean }>`
  text-transform: uppercase;
  font-size: 0.75rem;
  color: ${({$isSelf, theme}) =>
  $isSelf ? '#999999' : theme?.palette?.secondary};
`;

const MessageContainer = styled.div<{ $isSelf: boolean }>`
  padding-right: 1rem;
  font-size: 0.875rem;
  color: ${({$isSelf, theme}) =>
  $isSelf ? '#333333' : theme?.palette?.primary};
  white-space: pre-line;
`;

type ChatMessageProps = {
  name: string;
  message: string;
  isSelf: boolean;
  hideName: boolean;
};

export const ChatMessage: React.FC<ChatMessageProps> = ({
                                                          name,
                                                          message,
                                                          isSelf,
                                                          hideName,
                                                        }) => {
  return (
    <ChatMessageContainer $hideName={hideName}>
      {!hideName && <NameContainer $isSelf={isSelf}>{name}</NameContainer>}
      <MessageContainer $isSelf={isSelf}>{message}</MessageContainer>
    </ChatMessageContainer>
  );
};
