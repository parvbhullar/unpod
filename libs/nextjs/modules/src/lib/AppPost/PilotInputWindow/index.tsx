import {
  type ChangeEvent,
  Fragment,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Badge,
  Button,
  Dropdown,
  Form,
  Row,
  Space,
  Tooltip,
  Typography,
  Upload,
} from 'antd';
import {
  MdArrowForward,
  MdClose,
  MdDelete,
  MdOutlineAttachment,
} from 'react-icons/md';
import { BsArrowReturnLeft } from 'react-icons/bs';
import { uploadDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { AskAttachmentTypes } from '@unpod/constants';
import { POST_CONTENT_TYPE, POST_TYPE } from '@unpod/constants/AppEnums';
import AppLoader from '@unpod/components/common/AppLoader';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import {
  StyledBottomBar,
  StyledContentWrapper,
  StyledInput,
  StyledInputWrapper,
  StyledParent,
  StyledParentContainer,
  StyledPilotContainer,
  StyledPilotRoot,
} from './index.styled';
import UserAvatar from '@unpod/components/common/UserAvatar';
import { useOutsideClick } from '@unpod/custom-hooks';
import { RiVoiceprintLine } from 'react-icons/ri';

const { Item, useForm } = Form;
const { Paragraph, Text } = Typography;

type PilotInputWindowProps = {
  currentPost: any;
  replyParent: any;
  setReplyParent: (value: any) => void;
  sendJsonMessage: (value: any) => void;
  onStartVoice?: (options?: any) => void;
  repliesRef: { current?: { resetSystemMessage?: () => void } };
  children?: ReactNode;
};

const PilotInputWindow = ({
  currentPost,
  replyParent,
  setReplyParent,
  sendJsonMessage,
  onStartVoice,
  repliesRef,
  children,
}: PilotInputWindowProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [, setFocused] = useState(false);
  const [newQuery, setNewQuery] = useState<string | null>(null);
  const [requestPilot, setRequestedPilot] = useState<string | null>(null);
  const [form] = useForm();
  const [attachments, setAttachments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [hasNewline, setHasNewline] = useState(false);

  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<any>(null);

  useOutsideClick(wrapperRef, () => {
    if (!replyParent?.block_id) setFocused(false);
  });

  useEffect(() => {
    if (currentPost?.slug) {
      setFocused(false);
      const pilot =
        currentPost?.related_data?.pilot ||
        (currentPost.post_type === POST_TYPE.TASK ||
        currentPost.post_type === POST_TYPE.ASK
          ? 'multi-ai'
          : null);
      setRequestedPilot(pilot);
    }
  }, [currentPost]);

  useEffect(() => {
    if (replyParent?.thread_id) {
      setFocused(true);
    }
  }, [replyParent]);

  const uploadAttachments = (callbackFun: (data: any) => void, data: any) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi(`media/upload-multiple/`, infoViewActionsContext, formData)
      .then((res: any) => {
        data.files = res.data;
        setAttachments([]);
        callbackFun(data);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const submitQuestion = (data: any) => {
    repliesRef.current?.resetSystemMessage?.();
    const parentData: Record<string, any> = {};
    const pilot = replyParent?.user?.user_id || requestPilot || '';

    if (replyParent?.block_id) {
      parentData.parent_id = replyParent.block_id;
    }

    const { execution_type, focus } = currentPost?.related_data || {};

    const newMsg = {
      event: 'block',
      pilot: pilot,
      execution_type: execution_type || '',
      focus: focus || '',
      data: {
        block: 'html',
        content_type: 'question',
        block_type: pilot ? 'question' : 'text_msg',
        data: data,
        ...parentData,
      },
    };

    sendJsonMessage(newMsg);

    if (replyParent) setReplyParent({ ...replyParent, block_id: null });
    setNewQuery(null);
    setFocused(false);
    setLoading(false);
    form.resetFields();
  };

  const onQuerySubmit = (values: any = null) => {
    if (values && Object.keys(values).length > 0) {
      setLoading(true);

      const { focus } = currentPost?.related_data || {};

      const data = {
        content: values.content,
        focus: focus || '',
        knowledge_bases:
          currentPost?.knowledge_bases.map((kb: any) => kb.slug) || [],
        space: {
          space_token: currentPost?.space?.token,
          org_token: currentPost?.organization?.token,
          org_id: currentPost?.organization?.org_id,
        },
      };

      if (attachments?.length) {
        uploadAttachments(submitQuestion, data);
      } else {
        submitQuestion(data);
      }
    }
  };

  const handleAttachmentChange = (file: any) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      AskAttachmentTypes &&
      !AskAttachmentTypes.includes(extension) &&
      (!file.type ||
        (!AskAttachmentTypes.includes(file.type) &&
          !AskAttachmentTypes.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(`File type is now allowed`);
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event: MouseEvent, file: any) => {
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
          <Text style={{ marginRight: 5 }}>{item.name}</Text>
          <MdDelete
            fontSize={18}
            onClick={(event) => onAttachmentRemove(event, item)}
          />
        </Row>
      ),
    }));
  }, [attachments]);

  const isEnabled = (newQuery?.length ?? 0) > 2;

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setNewQuery(value);

    if (!value.trim()) {
      setHasNewline(false);
      return;
    }

    if (inputRef.current) {
      const el =
        inputRef.current.resizableTextArea?.textArea || inputRef.current;

      const style = window.getComputedStyle(el);
      const lineHeight = parseInt(style.lineHeight, 10);
      const baseHeight = lineHeight * 1.5;
      const currentHeight = el.scrollHeight;

      setHasNewline((prev) => prev || currentHeight > baseHeight + 5);
    }
  };

  return (
    <Fragment>
      <StyledPilotRoot ref={wrapperRef}>
        {children}
        <Form onFinish={onQuerySubmit} form={form}>
          <StyledPilotContainer className={hasNewline ? 'SetBottom' : ''}>
            {replyParent && (
              <StyledParentContainer>
                <Tooltip title={`Replying to ${replyParent.user.full_name}`}>
                  <StyledParent>
                    <BsArrowReturnLeft fontSize={16} />
                    <UserAvatar
                      user={replyParent.user}
                      size={24}
                      style={{ fontSize: 10 }}
                    />

                    <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                      {replyParent.title
                        ? replyParent.title
                        : getStringFromHtml(replyParent?.data?.content)}
                    </Paragraph>

                    <Button
                      type="text"
                      icon={<MdClose fontSize={16} />}
                      size="small"
                      onClick={() => setReplyParent(null)}
                    />
                  </StyledParent>
                </Tooltip>
                {/*<StyledDivider />*/}
              </StyledParentContainer>
            )}

            <StyledContentWrapper className={hasNewline ? 'SetBottom' : ''}>
              <Item name="content" style={{ flex: 1 }} noStyle>
                <StyledInputWrapper>
                  <StyledInput
                    bordered={false}
                    className={hasNewline ? 'SetBottom' : ''}
                    ref={inputRef}
                    placeholder={
                      currentPost.post_type === POST_TYPE.TASK ||
                      currentPost.post_type === POST_TYPE.ASK
                        ? 'Ask a followup...'
                        : 'Ask a question...'
                    }
                    autoSize={{ minRows: 1, maxRows: 10 }}
                    value={newQuery ?? ''}
                    onChange={handleChange}
                    onPressEnter={(e: KeyboardEvent<HTMLTextAreaElement>) => {
                      if (!e.shiftKey) {
                        e.preventDefault();
                        form.submit();
                      }
                    }}
                  />
                </StyledInputWrapper>
              </Item>

              <StyledBottomBar className={hasNewline ? 'SetBottom' : ''}>
                <Space size="small" align="center">
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
                            icon={<MdOutlineAttachment fontSize={18} />}
                          />
                        </Badge>
                      </Dropdown>
                    ) : (
                      <Button
                        type={attachments?.length ? 'primary' : 'default'}
                        shape="circle"
                        size="small"
                        icon={<MdOutlineAttachment fontSize={18} />}
                      />
                    )}
                  </Upload>

                  {currentPost.content_type === POST_CONTENT_TYPE.VOICE && (
                    <Button
                      type={isEnabled ? 'primary' : 'default'}
                      shape="circle"
                      size="small"
                      onClick={() => onStartVoice?.(true as any)}
                      icon={<RiVoiceprintLine fontSize={18} />}
                    />
                  )}

                  {newQuery && (
                    <Button
                      type={isEnabled ? 'primary' : 'default'}
                      shape="circle"
                      size="small"
                      htmlType="submit"
                      icon={<MdArrowForward fontSize={18} />}
                    />
                  )}
                </Space>
              </StyledBottomBar>
            </StyledContentWrapper>
          </StyledPilotContainer>
        </Form>
      </StyledPilotRoot>

      {loading && <AppLoader />}
    </Fragment>
  );
};

export default PilotInputWindow;
