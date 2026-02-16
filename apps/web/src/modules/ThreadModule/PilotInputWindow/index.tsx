import type {
  Dispatch,
  MouseEvent,
  MutableRefObject,
  SetStateAction,
} from 'react';
import { Fragment, useEffect, useMemo, useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import clsx from 'clsx';
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
import { POST_TYPE } from '@unpod/constants/AppEnums';
import AppLoader from '@unpod/components/common/AppLoader';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import {
  StyledBottomBar,
  StyledDivider,
  StyledInput,
  StyledParent,
  StyledParentContainer,
  StyledPilotContainer,
  StyledPilotRoot,
} from './index.styled';
import UserAvatar from '@unpod/components/common/UserAvatar';
import { useOutsideClick } from '@unpod/custom-hooks';
import type { RcFile } from 'antd/es/upload/interface';
import type { Thread } from '@unpod/constants/types';

const { Item, useForm } = Form;
const { Paragraph, Text } = Typography;

type ReplyParent = {
  block_id?: string | null;
  thread_id?: string;
  title?: string;
  data?: { content?: string };
  user: {
    full_name?: string;
    user_id?: string;
    [key: string]: unknown;
  };
};

type PilotInputWindowProps = {
  currentPost: Thread | null;
  replyParent: ReplyParent | null;
  setReplyParent: Dispatch<SetStateAction<ReplyParent | null>>;
  sendJsonMessage: (message: unknown) => void;
  repliesRef: MutableRefObject<{ resetSystemMessage?: () => void } | null>;
};

type QueryPayload = {
  content: string;
  focus: string;
  knowledge_bases: string[];
  files?: unknown;
};

const PilotInputWindow = ({
  currentPost,
  replyParent,
  setReplyParent,
  sendJsonMessage,
  repliesRef,
}: PilotInputWindowProps) => {
  const { formatMessage } = useIntl();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [focused, setFocused] = useState(false);
  const [newQuery, setNewQuery] = useState('');
  const [requestPilot, setRequestedPilot] = useState<string | null>(null);
  const [form] = useForm();
  const [attachments, setAttachments] = useState<RcFile[]>([]);
  const [loading, setLoading] = useState(false);

  const wrapperRef = useRef<HTMLDivElement | null>(null);

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

  const uploadAttachments = (
    callbackFun: (data: QueryPayload) => void,
    data: QueryPayload,
  ) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi<unknown[]>(
      `media/upload-multiple/`,
      infoViewActionsContext,
      formData,
    )
      .then((res) => {
        data.files = res.data;
        setAttachments([]);
        callbackFun(data);
      })
      .catch((response: { message?: string }) => {
        infoViewActionsContext.showError(response.message || 'Upload failed');
      });
  };

  const submitQuestion = (data: QueryPayload) => {
    repliesRef.current?.resetSystemMessage?.();
    const parentData: { parent_id?: string } = {};
    const pilot = replyParent?.user?.user_id || requestPilot || '';

    if (replyParent?.block_id) {
      parentData.parent_id = replyParent.block_id;
    }

    const newMsg = {
      event: 'block',
      pilot: pilot,
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
    setNewQuery('');
    setFocused(false);
    setLoading(false);
    form.resetFields();
  };

  const onQuerySubmit = (values: { content?: string } | null = null) => {
    if (values && Object.keys(values).length > 0) {
      setLoading(true);
      const data: QueryPayload = {
        content: values.content || '',
        focus: currentPost?.related_data?.focus || '',
        knowledge_bases:
          currentPost?.knowledge_bases
            ?.map((kb) => kb.slug || '')
            .filter(Boolean) || [],
      };

      if (attachments?.length) {
        uploadAttachments(submitQuestion, data);
      } else {
        submitQuestion(data);
      }
    }
  };

  const onFocused = () => {
    setFocused(true);
  };

  const handleAttachmentChange = (file: RcFile) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      AskAttachmentTypes &&
      !AskAttachmentTypes.includes(extension) &&
      (!file.type ||
        (!AskAttachmentTypes.includes(file.type) &&
          !AskAttachmentTypes.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event: MouseEvent, file: RcFile) => {
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

  const isEnabled = newQuery.length > 2;

  return (
    <Fragment>
      <StyledPilotRoot ref={wrapperRef}>
        <Form onFinish={onQuerySubmit} form={form}>
          <StyledPilotContainer
            onFocus={onFocused}
            onMouseDown={onFocused}
            className={clsx({ focused: focused })}
          >
            {replyParent && (
              <StyledParentContainer>
                <Tooltip
                  title={formatMessage(
                    { id: 'ask.replyingTo' },
                    { name: replyParent.user.full_name },
                  )}
                >
                  <StyledParent>
                    <BsArrowReturnLeft fontSize={16} />
                    <UserAvatar
                      user={replyParent.user}
                      size={24}
                      style={{ fontSize: 10 }}
                    />

                    <Paragraph type="secondary" ellipsis>
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
                <StyledDivider />
              </StyledParentContainer>
            )}

            <Item name="content">
              <StyledInput
                placeholder={formatMessage({ id: 'ask.askFollowup' })}
                variant="borderless"
                autoSize={{ minRows: 1, maxRows: 10 }}
                onPressEnter={form.submit}
                value={newQuery}
                onChange={(e) => setNewQuery(e.target.value)}
              />
            </Item>

            <StyledBottomBar>
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

                <Button
                  type={isEnabled ? 'primary' : 'default'}
                  shape="circle"
                  size="small"
                  htmlType="submit"
                  icon={<MdArrowForward fontSize={18} />}
                />
              </Space>
            </StyledBottomBar>
          </StyledPilotContainer>
        </Form>
      </StyledPilotRoot>

      {loading && <AppLoader />}
    </Fragment>
  );
};

export default PilotInputWindow;
