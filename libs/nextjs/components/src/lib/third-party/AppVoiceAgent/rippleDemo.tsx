import React, { useState } from 'react';
import styled from 'styled-components';

// Styled Components
const ChatContainer = styled.div`
  background: white;
  width: 700px;
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 20px;
  box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden; // Keeps overlay inside
`;

const InputField = styled.input`
  flex: 1;
  font-size: 18px;
  padding: 10px;
  border: none;
  outline: none;
  background: transparent;
  color: #333;
`;

const IconWrapper = styled.div`
  margin-right: 12px;
  color: gray;
`;

const SubmitButton = styled.button`
  background: #937cff;
  color: white;
  font-size: 16px;
  padding: 12px 24px;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  transition: background 0.3s ease-in-out;
  display: flex;
  align-items: center;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);

  &:hover {
    background: #7a5fff;
  }
`;

const Overlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
  border-radius: 20px;
  opacity: ${(props) => (props.show ? 1 : 0)};
  z-index: ${(props) => (props.show ? 2000000 : 0)};
  transform: ${(props) => (props.show ? 'scale(1)' : 'scale(0.5)')};
  transition: opacity 0.4s ease-in-out, transform 0.3s ease-in-out;
`;

const PostTitle = styled.h2`
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 5px;
`;

const PostContent = styled.p`
  font-size: 16px;
  color: #666;
  margin-bottom: 12px;
`;

const AuthorInfo = styled.div`
  display: flex;
  align-items: center;
  font-size: 14px;
  color: gray;
  font-weight: bold;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #555;

  &:hover {
    color: black;
  }
`;

const ChatInputComponent = () => {
  const [showOverlay, setShowOverlay] = useState(false);

  return (
    <ChatContainer>
      <InputField type="text" placeholder="Ask me anything..." />
      <IconWrapper>hi</IconWrapper>
      <SubmitButton onClick={() => setShowOverlay(true)}>Talk →</SubmitButton>

      {/* Overlay with Post Info */}
      <Overlay show={showOverlay}>
        <CloseButton onClick={() => setShowOverlay(false)}>×</CloseButton>
        <PostTitle>This is a test post</PostTitle>
        <PostContent>This is a test post</PostContent>
        <PostContent>This is a test post</PostContent>
        <PostContent>This is a test post</PostContent>
        <PostContent>This is a test post</PostContent>
        <AuthorInfo>(O) Yogendra Singh · 2 years ago</AuthorInfo>
      </Overlay>
    </ChatContainer>
  );
};

export default ChatInputComponent;
