import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatMessageInput } from './ChatMessageInput';
import styled from 'styled-components';
import SimpleBar from 'simplebar-react';

const inputHeight = 33;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  //height: 100vh;
`;

const MessagesContainer = styled(SimpleBar)`
  height: calc(100vh - 190px);
`;

const MessagesWrapper = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100%;
  justify-content: flex-end;
  padding: 16px !important;
`;

type ChatMessage = {
  name: string;
  message: string;
  isSelf: boolean;};

type ChatTileProps = {
  messages: ChatMessage[];
  onSend?: (message: string) => void;};

export const ChatTile: React.FC<ChatTileProps> = ({ messages, onSend }) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [scrollRef, messages]);

  return (
    <Container>
      <MessagesContainer scrollableNodeProps={{ ref: scrollRef }}>
        <MessagesWrapper>
          {messages.map((message, index, allMsg) => {
            const hideName =
              index >= 1 && allMsg[index - 1].name === message.name;

            return (
              <ChatMessage
                key={index}
                hideName={hideName}
                name={message.name}
                message={message.message}
                isSelf={message.isSelf}
              />
            );
          })}
        </MessagesWrapper>
      </MessagesContainer>
      <ChatMessageInput
        height={inputHeight}
        placeholder="common.typeMessage"
        onSend={onSend}
      />
    </Container>
  );
};
