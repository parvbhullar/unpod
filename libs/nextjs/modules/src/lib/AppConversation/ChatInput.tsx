'use client';
import type {ChangeEvent, KeyboardEvent, MouseEvent, ReactNode} from 'react';
import {useEffect, useMemo, useRef, useState} from 'react';
import {SendOutlined} from '@ant-design/icons';
import {ChatInputBox, ChatSendButton} from './index.styled';
import {
  StyledBottomBar,
  StyledContentWrapper,
  StyledInputWrapper,
  StyledPilotContainer,
  StyledPilotRoot,
} from '../AppPost/PilotInputWindow/index.styled';
import {Badge, Button, Dropdown, Row, Typography, Upload} from 'antd';
import type {TextAreaRef} from 'antd/es/input/TextArea';
import type {RcFile, UploadProps} from 'antd/es/upload/interface';
import {AskAttachmentTypes} from '@unpod/constants';
import {MdDelete, MdOutlineAttachment} from 'react-icons/md';
import {RiVoiceprintLine} from 'react-icons/ri';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import {uploadDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {useIntl} from 'react-intl';

const {Text} = Typography;

type ChatInputPayload = {
  content: string;
  files?: unknown;
};

type ChatInputProps = {
  onSend: (payload: ChatInputPayload) => void;
  disabled?: boolean;
  thinking?: boolean;
  onStartVoice?: (start: boolean) => void;
  isGeneratingToken?: boolean;
  children?: ReactNode;
};

const ChatInput = ({
                     onSend,
                     disabled,
                     onStartVoice,
                     thinking,
                     isGeneratingToken,
                     children,
                   }: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<TextAreaRef | null>(null);
  const infoViewActionsContext = useInfoViewActionsContext();
  const [attachments, setAttachments] = useState<RcFile[]>([]);
  const [hasNewline, setHasNewline] = useState(false);
  const [uploading, setUploading] = useState(false);
  const shouldFocusRef = useRef(false);
  const {formatMessage} = useIntl();

  const uploadAttachments = (callback: (files: unknown) => void) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    setUploading(true);

    uploadDataApi(`media/upload-multiple/`, infoViewActionsContext, formData)
      .then((res: any) => {
        setAttachments([]);
        callback(res?.data);
      })
      .catch((response) => {
        infoViewActionsContext.showError(
          response.message || formatMessage({id: 'bridge.uploadFailed'}),
        );
      })
      .finally(() => {
        setUploading(false);
      });
  };

  const sendMessage = (files?: unknown) => {
    const messageData: ChatInputPayload = {
      content: message.trim(),
      ...(files ? {files} : {}),
    };
    console.log('sending message', messageData);
    onSend(messageData);
    shouldFocusRef.current = true;
    setMessage('');
    setHasNewline(false);
  };

  const handleSubmit = () => {
    if ((message.trim() || attachments.length > 0) && !disabled && !uploading) {
      if (attachments.length > 0) {
        uploadAttachments(sendMessage);
      } else {
        sendMessage();
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;

    if (!value.trim()) {
      setHasNewline(false);
      return;
    }

    const textArea = textareaRef.current?.resizableTextArea?.textArea;
    if (textArea) {
      const style = window.getComputedStyle(textArea);
      const lineHeight = parseInt(style.lineHeight, 10);
      const baseHeight = lineHeight * 1.5;
      const currentHeight = textArea.scrollHeight;

      setHasNewline((prev) => prev || currentHeight > baseHeight + 5);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    // Auto-resize textarea
    // if (textareaRef.current) {
    //   textareaRef.current.style.height = 'auto';
    //   textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    // }
  };

  // Maintain focus on input after sending message
  useEffect(() => {
    if (shouldFocusRef.current && !disabled && !uploading) {
      console.log('🔍 Focusing input after send');
      shouldFocusRef.current = false;

      // Use multiple timing strategies to ensure focus
      const focusInput = () => {
        if (textareaRef.current) {
          const textArea = textareaRef.current.resizableTextArea?.textArea;
          if (textArea) {
            textArea.focus();
            console.log(
              '✅ Input focused, activeElement:',
              document.activeElement,
            );
          }
        }
      };

      // Immediate focus attempt
      focusInput();

      // Backup focus with requestAnimationFrame
      requestAnimationFrame(focusInput);

      // Final backup with setTimeout
      setTimeout(focusInput, 10);
    }
  }, [message, disabled, uploading]);

  // useEffect(() => {
  //   if (!thinking && textareaRef.current) {
  //     textareaRef.current.focus();
  //   }
  // }, [thinking]);

  const handleAttachmentChange: UploadProps['beforeUpload'] = (file) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    const extensionValue = extension ?? '';
    const allowedTypes = AskAttachmentTypes;
    const isAllowed = !allowedTypes
      ? true
      : Array.isArray(allowedTypes)
        ? allowedTypes.includes(extensionValue) ||
        (!!file.type &&
          (allowedTypes.includes(file.type) ||
            allowedTypes.includes(file.type.split('/')[0])))
        : allowedTypes.includes(extensionValue) ||
        (!!file.type &&
          (allowedTypes.includes(file.type) ||
            allowedTypes.split('/').includes(file.type.split('/')[0])));

    if (!isAllowed) {
      infoViewActionsContext.showError(
        formatMessage({id: 'upload.errorInvalidFileType'}),
      );
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event: MouseEvent<SVGElement>, file: RcFile) => {
    event.stopPropagation();
    setAttachments((prevState) =>
      prevState.filter((item) => item.uid !== file.uid),
    );
  };

  const attachmentsList = useMemo(() => {
    return attachments.map((item) => ({
      key: item.uid,
      label: (
        <Row justify="space-between" align="middle">
          <Text style={{marginRight: 5}}>{item.name}</Text>
          <MdDelete
            fontSize={18}
            onClick={(event) => onAttachmentRemove(event, item)}
          />
        </Row>
      ),
    }));
  }, [attachments]);

  return (
    <StyledPilotRoot>
      <StyledPilotContainer className={hasNewline ? 'SetBottom' : ''}>
        <StyledContentWrapper className={hasNewline ? 'SetBottom' : ''}>
          <StyledInputWrapper className={hasNewline ? 'SetBottom' : ''}>
            <ChatInputBox
              bordered={false}
              ref={textareaRef}
              autoSize={{minRows: 1, maxRows: 10}}
              value={message}
              onChange={(e) => {
                handleChange(e);
                handleInputChange(e);
              }}
              onKeyDown={handleKeyDown}
              placeholder={
                uploading
                  ? formatMessage({id: 'common.uploading'})
                  : disabled
                    ? formatMessage({id: 'common.wait'})
                    : formatMessage({id: 'chat.typeMessage'})
              }
              disabled={disabled || uploading}
            />
          </StyledInputWrapper>

          <StyledBottomBar className={hasNewline ? 'SetBottom' : ''}>
            <Upload
              name="files"
              accept={AskAttachmentTypes}
              maxCount={10}
              beforeUpload={handleAttachmentChange}
              showUploadList={false}
              multiple
            >
              {attachments?.length > 0 ? (
                <Dropdown
                  menu={{
                    items: attachmentsList,
                  }}
                  trigger={['hover']}
                  placement="top"
                  arrow
                >
                  <Badge
                    count={attachments?.length}
                    size="small"
                    offset={[-5, 2]}
                  >
                    <Button
                      type={attachments?.length ? 'primary' : 'default'}
                      shape="circle"
                      size="small"
                      icon={<MdOutlineAttachment fontSize={18}/>}
                    />
                  </Badge>
                </Dropdown>
              ) : (
                <Button
                  type={attachments?.length ? 'primary' : 'default'}
                  shape="circle"
                  size="small"
                  icon={<MdOutlineAttachment fontSize={18}/>}
                />
              )}
            </Upload>

            {message || attachments?.length > 0 ? (
              <ChatSendButton
                type="primary"
                ghost
                onClick={handleSubmit}
                disabled={
                  uploading ||
                  disabled ||
                  (attachments?.length === 0 && !message.trim())
                }
                $hasContent={!!message.trim()}
                icon={<SendOutlined/>}
              />
            ) : children ? (
              children
            ) : (
              <Button
                shape="circle"
                size="small"
                loading={isGeneratingToken}
                onClick={() => onStartVoice?.(true)}
                icon={<RiVoiceprintLine fontSize={18}/>}
              />
            )}
          </StyledBottomBar>
        </StyledContentWrapper>
      </StyledPilotContainer>
    </StyledPilotRoot>
  );
};

export default ChatInput;
