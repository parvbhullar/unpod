import React, {useCallback, useRef, useState} from 'react';
import styled from 'styled-components';
import {Button, Input, type InputRef} from 'antd';
import {useIntl} from 'react-intl';

const Container = styled.div<{ $height?: number }>`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  height: ${({$height}) => ($height ? `${$height}px` : 'auto')};
  padding: 0 16px !important;
`;

const InputRow = styled.div`
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  position: relative;
`;

const Cursor = styled.div<{ $inputHasFocus: boolean }>`
  width: 0.5rem;
  height: 1rem;
  background-color: ${({$inputHasFocus, theme}) =>
  $inputHasFocus ? theme?.palette?.primary : '#1f2937'};
  position: absolute;
  left: 0.5rem;
`;

const HiddenInput = styled.span`
  position: absolute;
  top: 0;
  left: 0;
  font-size: 0.75rem;
  padding-left: 0.75rem;
  color: #f59e0b;
  pointer-events: none;
  opacity: 0;
`;

type ChatMessageInputProps = {
  placeholder?: string;
  height?: number;
  onSend?: (message: string) => void;
};

export const ChatMessageInput: React.FC<ChatMessageInputProps> = ({
                                                                    placeholder,
                                                                    height,
                                                                    onSend,
                                                                  }) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef<InputRef | null>(null);
  const [inputHasFocus, setInputHasFocus] = useState(false);
  const {formatMessage} = useIntl();

  const handleSend = useCallback(() => {
    if (!onSend) {
      return;
    }
    if (message === '') {
      return;
    }

    onSend(message);
    setMessage('');
  }, [onSend, message]);

  return (
    <Container $height={height}>
      <InputRow>
        <Cursor $inputHasFocus={inputHasFocus}/>
        <Input
          ref={inputRef}
          placeholder={formatMessage({id: placeholder})}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onFocus={() => setInputHasFocus(true)}
          onBlur={() => setInputHasFocus(false)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSend();
            }
          }}
        />
        <HiddenInput>{message.replaceAll(' ', '\u00a0')}</HiddenInput>
        <Button
          size="small"
          color="primary"
          variant="solid"
          disabled={message.length === 0 || !onSend}
          onClick={handleSend}
        >
          {formatMessage({id: 'common.send'})}
        </Button>
      </InputRow>
    </Container>
  );
};
